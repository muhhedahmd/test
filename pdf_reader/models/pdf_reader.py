import base64
import json
from odoo import models, fields, api
from google import genai
from google.genai import types

class PdfReaderLine(models.TransientModel):
    _name = 'pdf.reader.line'
    _description = 'PDF Reader Line Wizard'

    reader_id = fields.Many2one('pdf.reader', string='Reader', ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Matched Product')
    col1 = fields.Char(string='Description / Product')
    col2 = fields.Char(string='Quantity')
    col3 = fields.Char(string='Price')
    col4 = fields.Char(string='Taxes')
    col5 = fields.Char(string='Total')

class PdfReader(models.TransientModel):
    _name = 'pdf.reader'
    _description = 'PDF Reader Wizard using Gemini'

    document_type = fields.Selection([
        ('invoice', 'Vendor Bill / Invoice'),
    ], string='Document Type', default='invoice', required=True)
    
    attachment_ids = fields.Many2many('ir.attachment', string='Upload Files (PDFs/Images)', required=True)
    
    prompt = fields.Text(string='Prompt', default='Extract the invoice data.')
    
    # Preview Fields
    partner_name = fields.Char(string='Extracted Partner Name')
    partner_id = fields.Many2one('res.partner', string='Matched Partner')
    invoice_date = fields.Date(string='Extracted Date')
    invoice_ref = fields.Char(string='Extracted Reference')
    warning_message = fields.Char(string='Warning Message', readonly=True)
    
    result = fields.Text(string='Raw AI Result', readonly=True)
    line_ids = fields.One2many('pdf.reader.line', 'reader_id', string='Extracted Lines')

    def action_read_pdf(self):
        for record in self:
            if not record.attachment_ids:
                continue

            record.line_ids.unlink()

            # Prepare files for Gemini Native Vision
            contents = []
            for attachment in record.attachment_ids:
                if not attachment.datas:
                    continue
                # Guess mimetype if missing
                mime = attachment.mimetype or 'application/pdf'
                file_bytes = base64.b64decode(attachment.datas)
                contents.append(
                    types.Part.from_bytes(data=file_bytes, mime_type=mime)
                )

            # Send to Gemini API
            try:
                client = genai.Client(api_key="AQ.Ab8RN6LvI0jCjYexjREyBEJpNQp4mzKoIoH7S9kKS3beP5eXRA")

                if record.document_type == 'invoice':
                    system_instruction = (
                        "You are an expert AI extraction tool. Extract the invoice details from the attached documents. "
                        "Note: The text might be Arabic extracted backwards. Please read the numbers and text carefully. "
                        "You MUST reply strictly with a valid JSON object. Do NOT include markdown like ```json. "
                        "The JSON object must have this exact structure: "
                        "{ "
                        "  \"partner_name\": \"Name of the vendor/supplier (reverse the Arabic text to be readable if it is backwards)\", "
                        "  \"invoice_date\": \"YYYY-MM-DD format if found, else empty\", "
                        "  \"invoice_ref\": \"Invoice number or reference\", "
                        "  \"lines\": [ "
                        "    { \"description\": \"Product or service name\", \"quantity\": \"Numeric quantity\", \"price\": \"Unit price\", \"taxes\": \"Tax rate or amount\", \"total\": \"Line total\" } "
                        "  ] "
                        "}"
                    )
                else:
                    system_instruction = "Extract data to JSON."

                full_prompt = f"{system_instruction}\n\nUser Prompt: {record.prompt}\n\nPlease extract data from the provided files."
                contents.append(full_prompt)

                response = client.models.generate_content(
                    model="gemini-3.5-flash",
                    contents=contents
                )
                
                # Depending on the SDK version, it could be .text or .candidates[0].content.parts[0].text
                # .text is standard for google-genai
                response_text = response.text.strip()
                record.result = response_text

                clean_json = response_text
                if clean_json.startswith("```json"):
                    clean_json = clean_json[7:]
                if clean_json.endswith("```"):
                    clean_json = clean_json[:-3]
                clean_json = clean_json.strip()

                try:
                    data = json.loads(clean_json)
                    
                    # Update Preview Fields
                    if record.document_type == 'invoice':
                        record.partner_name = data.get('partner_name')
                        record.invoice_ref = data.get('invoice_ref')
                        if data.get('invoice_date'):
                            try:
                                record.invoice_date = fields.Date.to_date(data.get('invoice_date'))
                            except:
                                pass # ignore bad dates
                        
                        # Find Partner
                        partner = False
                        if record.partner_name:
                            partner = self.env['res.partner'].search([('name', 'ilike', record.partner_name)], limit=1)
                        record.partner_id = partner.id if partner else False

                        if record.partner_name and not partner:
                            record.warning_message = f"Warning: Vendor '{record.partner_name}' was not found. Please select manually."
                        else:
                            record.warning_message = False

                        # Update Lines
                        lines_data = data.get('lines', [])
                        lines_to_create = []
                        for row in lines_data:
                            desc = str(row.get('description', ''))
                            product = False
                            if desc:
                                product = self.env['product.product'].search([('name', 'ilike', desc)], limit=1)
                                
                            lines_to_create.append((0, 0, {
                                'col1': desc,
                                'product_id': product.id if product else False,
                                'col2': str(row.get('quantity', '')),
                                'col3': str(row.get('price', '')),
                                'col4': str(row.get('taxes', '')),
                                'col5': str(row.get('total', '')),
                            }))
                        record.write({'line_ids': lines_to_create})
                        
                except Exception as json_e:
                    record.result += f"\n\n--- JSON Parsing Error ---\nFailed to parse into preview fields.\nError: {json_e}"

            except Exception as e:
                record.result = f"Error calling Gemini API: {e}"

            return {
                'type': 'ir.actions.act_window',
                'res_model': 'pdf.reader',
                'view_mode': 'form',
                'res_id': record.id,
                'target': 'new',
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
                    
                line_val = {
                    'name': line.col1 or 'Extracted Item',
                    'quantity': qty,
                    'price_unit': price,
                }
                if line.product_id:
                    line_val['product_id'] = line.product_id.id
                    
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
