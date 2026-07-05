import base64
import json
from odoo import models, fields, api
from odoo.exceptions import UserError
from google import genai
from google.genai import types

class PdfReaderLine(models.Model):
    _name = 'pdf.reader.line'
    _description = 'PDF Reader Line Wizard'

    reader_id = fields.Many2one('pdf.reader', string='Reader', ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Matched Product')
    col1 = fields.Char(string='Description / Product')
    col2 = fields.Char(string='Quantity')
    col3 = fields.Char(string='Price')
    col4 = fields.Char(string='Taxes Amount')
    col5 = fields.Char(string='Total')
    col6 = fields.Char(string='Discount')
    col7 = fields.Char(string='Tax Rate (%)')
    amount_total = fields.Float(string='Line Total')

class PdfReader(models.Model):
    _name = 'pdf.reader'
    _description = 'PDF Reader using Gemini'
    _rec_name = 'invoice_ref'

    document_type = fields.Selection([
        ('invoice', 'Vendor Bill / Invoice'),
    ], string='Document Type', default='invoice', required=True)
    
    attachment_ids = fields.Many2many('ir.attachment', string='Upload Files (PDFs/Images)')
    
    prompt = fields.Text(string='Prompt', default='Extract the invoice data.')
    
    # Preview Fields
    partner_name = fields.Char(string='Extracted Partner Name')
    partner_id = fields.Many2one('res.partner', string='Matched Partner')
    invoice_date = fields.Date(string='Extracted Date')
    invoice_ref = fields.Char(string='Extracted Reference')
    warning_message = fields.Char(string='Warning Message', readonly=True)
    amount_total = fields.Float(string='Total Amount', compute='_compute_amount_total', store=True)
    
    result = fields.Text(string='Raw AI Result', readonly=True)
    line_ids = fields.One2many('pdf.reader.line', 'reader_id', string='Extracted Lines')

    @api.depends('line_ids.amount_total')
    def _compute_amount_total(self):
        for record in self:
            record.amount_total = sum(line.amount_total for line in record.line_ids)

    def _call_gemini(self, attachments):
        """Send the given attachments (a single document's files) to Gemini and
        return the raw response text. Returns (response_text, error_message)."""
        self.ensure_one()

        # Prepare files for Gemini Native Vision
        contents = []
        for attachment in attachments:
            if not attachment.datas:
                continue
            # Guess mimetype if missing
            mime = attachment.mimetype or 'application/pdf'
            file_bytes = base64.b64decode(attachment.datas)
            contents.append(
                types.Part.from_bytes(data=file_bytes, mime_type=mime)
            )

        api_key = self.env['ir.config_parameter'].sudo().get_param('pdf_reader.gemini_api_key')
        if not api_key:
            return None, "API Key not found. Please set 'pdf_reader.gemini_api_key' in Technical -> System Parameters."

        client = genai.Client(api_key=api_key)

        if self.document_type == 'invoice':
            system_instruction = (
                "You are an expert AI extraction tool. Extract the invoice details from the attached documents. "
                "Note: The text might be Arabic extracted backwards. Please read the numbers and text carefully. "
                "IMPORTANT: The attached file(s) belong to ONE SINGLE invoice/document only. "
                "You MUST reply strictly with a valid JSON object. Do NOT include markdown like ```json. "
                "The JSON object must have this exact structure: "
                "{ "
                "  \"partner_name\": \"Name of the vendor/supplier (reverse the Arabic text to be readable if it is backwards)\", "
                "  \"invoice_date\": \"YYYY-MM-DD format if found, else empty\", "
                "  \"invoice_ref\": \"Invoice number or reference\", "
                "  \"lines\": [ "
                "    { \"description\": \"Product or service name\", \"quantity\": \"Numeric quantity\", \"price\": \"Unit price\", \"discount\": \"Discount percentage or amount\", \"tax_rate\": \"Tax percentage (e.g. 15)\", \"taxes\": \"Tax amount\", \"total\": \"Line total\" } "
                "  ] "
                "}"
            )
        else:
            system_instruction = "Extract data to JSON."

        full_prompt = f"{system_instruction}\n\nUser Prompt: {self.prompt}\n\nPlease extract data from the provided files."
        contents.append(full_prompt)

        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=contents
        )

        # Depending on the SDK version, it could be .text or .candidates[0].content.parts[0].text
        # .text is standard for google-genai
        return response.text.strip(), None

    def _apply_extracted_data(self, response_text):
        """Parse the Gemini JSON response and populate this single record's
        preview fields and lines."""
        self.ensure_one()
        self.result = response_text

        clean_json = response_text
        if clean_json.startswith("```json"):
            clean_json = clean_json[7:]
        if clean_json.endswith("```"):
            clean_json = clean_json[:-3]
        clean_json = clean_json.strip()

        try:
            data = json.loads(clean_json)
        except Exception as json_e:
            self.result = f"{self.result}\n\n--- JSON Parsing Error ---\nFailed to parse into preview fields.\nError: {json_e}"
            return

        if self.document_type != 'invoice':
            return

        self.partner_name = data.get('partner_name')
        self.invoice_ref = data.get('invoice_ref')
        if data.get('invoice_date'):
            try:
                self.invoice_date = fields.Date.to_date(data.get('invoice_date'))
            except Exception:
                pass  # ignore bad dates

        # Find Partner
        partner = False
        if self.partner_name:
            partner = self.env['res.partner'].search([('name', 'ilike', self.partner_name)], limit=1)
        self.partner_id = partner.id if partner else False

        if self.partner_name and not partner:
            self.warning_message = f"Warning: Vendor '{self.partner_name}' was not found. Please select manually."
        else:
            self.warning_message = False

        # Update Lines
        lines_data = data.get('lines', [])
        lines_to_create = []
        for row in lines_data:
            desc = str(row.get('description', ''))
            product = False
            if desc:
                product = self.env['product.product'].search([('name', 'ilike', desc)], limit=1)

            line_amount_total = 0.0
            if row.get('total'):
                import re
                match = re.search(r'(\d+(?:\.\d+)?)', str(row.get('total', '')))
                if match:
                    line_amount_total = float(match.group(1))

            lines_to_create.append((0, 0, {
                'col1': desc,
                'product_id': product.id if product else False,
                'col2': str(row.get('quantity', '')),
                'col3': str(row.get('price', '')),
                'col4': str(row.get('taxes', '')),
                'col5': str(row.get('total', '')),
                'col6': str(row.get('discount', '')),
                'col7': str(row.get('tax_rate', '')),
                'amount_total': line_amount_total,
            }))
        self.write({'line_ids': lines_to_create})

    def action_read_pdf(self):
        """Extract data from the uploaded file(s).

        FIX: previously, when several files were uploaded on the same record,
        ALL of them were sent to Gemini in a single call and merged into one
        JSON result - so uploading several separate invoices at once produced
        wrong/mixed-up data (only one invoice's worth of lines, or fields
        from different invoices blended together).

        Now each uploaded file is treated as its OWN document: if more than
        one attachment is present, we create one 'pdf.reader' record per
        file (each with a single attachment) and run the extraction on each
        one independently. A single uploaded file keeps working exactly as
        before, on the current record.
        """
        processed_ids = []

        for record in self:
            if not record.attachment_ids:
                raise UserError("Please upload at least one file before extracting data!")

            attachments = record.attachment_ids

            if len(attachments) > 1:
                targets = []
                for index, attachment in enumerate(attachments):
                    if index == 0:
                        # Reuse the current record for the first file.
                        rec = record
                        rec.attachment_ids = [(6, 0, [attachment.id])]
                    else:
                        # Create a sibling record for every extra file so
                        # each PDF becomes its own separate extraction.
                        rec = record.copy({
                            'attachment_ids': [(6, 0, [attachment.id])],
                            'line_ids': [(5, 0, 0)],
                            'result': False,
                            'warning_message': False,
                        })
                    targets.append(rec)
            else:
                targets = [record]

            for rec in targets:
                rec.line_ids.unlink()
                try:
                    response_text, error = rec._call_gemini(rec.attachment_ids)
                    if error:
                        rec.result = error
                        continue
                    rec._apply_extracted_data(response_text)
                except Exception as e:
                    rec.result = f"Error calling Gemini API: {e}"
                processed_ids.append(rec.id)

        if len(processed_ids) > 1:
            # Multiple documents were processed: show them all in a list
            # instead of leaving the user only looking at one record.
            return {
                'name': 'Extracted Documents',
                'view_mode': 'list,form',
                'res_model': 'pdf.reader',
                'domain': [('id', 'in', processed_ids)],
                'type': 'ir.actions.act_window',
                'target': 'current',
            }

    def action_create_invoice(self):
        for record in self:
            if record.document_type != 'invoice':
                continue

            # Prepare invoice lines
            invoice_line_vals = []
            for line in record.line_ids:
                qty = 1.0
                price = 0.0
                try:
                    qty = float(line.col2)
                except ValueError:
                    pass
                try:
                    price = float(line.col3)
                except ValueError:
                    pass
                    
                
                # Extract Discount
                disc = 0.0
                if line.col6:
                    import re
                    match = re.search(r'(\d+(?:\.\d+)?)', line.col6)
                    if match:
                        disc = float(match.group(1))

                # Extract Tax Rate and Apply/Create
                tax_ids = []
                if line.col7:
                    import re
                    match = re.search(r'(\d+(?:\.\d+)?)', line.col7)
                    if match:
                        rate = float(match.group(1))
                        if rate > 0:
                            tax = self.env['account.tax'].search([
                                ('amount', '=', rate), 
                                ('type_tax_use', '=', 'purchase')
                            ], limit=1)
                            if not tax:
                                tax = self.env['account.tax'].create({
                                    'name': f'VAT {rate}% (Auto-extracted)',
                                    'amount': rate,
                                    'type_tax_use': 'purchase',
                                })
                            tax_ids.append(tax.id)

                line_val = {
                    'name': line.col1 or 'Extracted Item',
                    'quantity': qty,
                    'price_unit': price,
                    'discount': disc,
                }
                if line.product_id:
                    line_val['product_id'] = line.product_id.id
                if tax_ids:
                    line_val['tax_ids'] = [(6, 0, tax_ids)]
                    
                invoice_line_vals.append((0, 0, line_val))

            move_vals = {
                'move_type': 'in_invoice', # Vendor Bill
                'ref': record.invoice_ref,
                'invoice_date': record.invoice_date,
                'invoice_line_ids': invoice_line_vals,
            }
            if record.partner_id:
                move_vals['partner_id'] = record.partner_id.id
                
            move = self.env['account.move'].create(move_vals)
            
            return {
                'name': 'Extracted Vendor Bill',
                'view_mode': 'form',
                'res_model': 'account.move',
                'res_id': move.id,
                'type': 'ir.actions.act_window',
                'target': 'current',
            }
