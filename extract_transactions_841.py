import json, re, pathlib, decimal
from dataclasses import dataclass, asdict
from typing import List, Dict

PAYLOAD_PATH = pathlib.Path(__file__).parent / 'debug_outputs' / '841_openai_payload.json'
OUTPUT_PATH = pathlib.Path(__file__).parent / 'debug_outputs' / '841_transactions.json'

DATE_LINE = re.compile(r'^(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])$')
AMOUNT_LINE = re.compile(r'^\d{1,3}(?:,\d{3})*\.\d{2}$')
CURRENCY_CLEAN = re.compile(r'[^0-9\.-]')

@dataclass
class Transaction:
    date: str           # MM-DD
    type: str           # debit / credit / fee
    amount: str         # original string amount
    amount_decimal: float
    description: str


def parse_transactions(text: str) -> Dict[str, List[Transaction]]:
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    n = len(lines)
    debits: List[Transaction] = []
    credits: List[Transaction] = []
    i = 0
    current_section = None
    while i < n:
        line = lines[i]
        upper = line.upper()
        if upper == 'DEBITS':
            current_section = 'debits'
        elif upper == 'CREDITS':
            current_section = 'credits'
        elif DATE_LINE.match(line):
            # Collect description lines until amount line or next date/section
            date_val = line
            desc_lines = []
            j = i + 1
            amount_line = None
            while j < n:
                nxt = lines[j]
                if AMOUNT_LINE.match(nxt):
                    amount_line = nxt
                    j += 1
                    break
                if DATE_LINE.match(nxt) or nxt.upper() in ('DEBITS','CREDITS','DAILY BALANCES','OVERDRAFT/RETURN ITEM FEES'):
                    break
                desc_lines.append(nxt)
                j += 1
            if amount_line and current_section in ('debits','credits'):
                amt_clean = CURRENCY_CLEAN.sub('', amount_line)
                try:
                    amt_dec = float(decimal.Decimal(amt_clean))
                except Exception:
                    amt_dec = 0.0
                description = ' | '.join(desc_lines)
                ttype = 'debit' if current_section == 'debits' else 'credit'
                # Classify fee but keep in original section (debits fees are still debits)
                if 'FEE' in description.upper() or 'LOSS/CHG' in description.upper():
                    ttype = 'fee'
                tx = Transaction(date=date_val, type=ttype, amount=amount_line, amount_decimal=amt_dec, description=description)
                # Fees go to debits if found in DEBITS section, credits if found in CREDITS section
                if current_section == 'debits':
                    debits.append(tx)
                else:
                    credits.append(tx)
            i = j - 1 if j>i else i
        i += 1

    return {
        'debits': debits,
        'credits': credits
    }


def main():
    data = json.loads(PAYLOAD_PATH.read_text(encoding='utf-8'))
    # 'messages'[-1]['content'] contains the user prompt with OCR text appended.
    ocr = ''
    for msg in data.get('messages', []):
        if msg.get('role') == 'user':
            ocr = msg.get('content','')
    # Remove prompt prefix up to 'FULL OCR TEXT:'
    marker = 'FULL OCR TEXT:'
    if marker in ocr:
        ocr = ocr.split(marker,1)[1]
    parsed = parse_transactions(ocr)
    out = {
        'debits': [asdict(t) for t in parsed['debits']],
        'credits': [asdict(t) for t in parsed['credits']],
        'total_debits': round(sum(t.amount_decimal for t in parsed['debits']),2),
        'total_credits': round(sum(t.amount_decimal for t in parsed['credits']),2),
        'count_debits': len(parsed['debits']),
        'count_credits': len(parsed['credits'])
    }
    OUTPUT_PATH.write_text(json.dumps(out, indent=2), encoding='utf-8')
    print(json.dumps(out, indent=2))

if __name__ == '__main__':
    main()
