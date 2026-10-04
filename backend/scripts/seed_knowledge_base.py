"""Seed Knowledge Base with Official GST/IT Act Documents.

This script ingests official tax law sources into the RAG knowledge base
for use in grounded notice drafting.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.app.knowledge.ingest import ingest_official_source
from backend.app.database import get_db, Base, engine


# Sample official sources - in production these would be full PDF/HTML documents
OFFICIAL_SOURCES = [
    {
        "title": "CGST Act, 2017 - Section 16 (Eligibility and conditions for taking input tax credit)",
        "source_type": "act",
        "url": "https://www.gst.gov.in/legal/acts-rules",
        "version": "2017",
        "content": """
Section 16: Eligibility and conditions for taking input tax credit.

(1) Every registered person shall, subject to such conditions and restrictions as may be prescribed and in the manner specified in section 49, be entitled to take credit of input tax charged on any supply of goods or services or both to him which are used or intended to be used in the course or furtherance of his business and the said amount shall be credited to the electronic credit ledger of such person.

(2) Notwithstanding anything contained in this section, no registered person shall be entitled to the credit of any input tax in respect of any supply of goods or services or both to him unless,—
(a) he is in possession of a tax invoice or debit note issued by a supplier registered under this Act, or such other tax paying documents as may be prescribed;
(b) he has received the goods or services or both;
(c) subject to the provisions of section 41, the tax charged in respect of such supply has been actually paid to the Government, either in cash or through utilisation of input tax credit admissible in respect of the said supply; and
(d) he has furnished the return under section 39.

(3) Where the goods against an invoice are received in lots or instalments, the registered person shall be entitled to take credit upon receipt of the last lot or instalment.

(4) Where a registered person fails to pay to the supplier of goods or services or both, the amount towards the value of supply along with tax payable thereon within a period of one hundred and eighty days from the date of issue of invoice by the supplier, an amount equal to the input tax credit availed by the recipient shall be added to his output tax liability, along with interest thereon, in such manner as may be prescribed.
        """.strip(),
    },
    {
        "title": "CGST Act, 2017 - Section 73 (Determination of tax not paid or short paid or erroneously refunded or input tax credit wrongly availed or utilised for any reason other than fraud)",
        "source_type": "act",
        "url": "https://www.gst.gov.in/legal/acts-rules",
        "version": "2017",
        "content": """
Section 73: Determination of tax not paid or short paid or erroneously refunded or input tax credit wrongly availed or utilised for any reason other than fraud.

(1) Where it appears to the proper officer that any tax has not been paid or short paid or erroneously refunded, or where input tax credit has been wrongly availed or utilised for any reason, other than the reason of fraud or any wilful misstatement or suppression of facts to evade tax, he shall serve notice on the person chargeable with tax which has not been so paid or which has been so short paid or to whom the refund has erroneously been made, or who has wrongly availed or utilised input tax credit, requiring him to show cause as to why he should not pay the amount specified in the notice along with interest payable thereon under section 50 and a penalty equivalent to ten per cent. of the tax or ten thousand rupees, whichever is higher.

(2) The proper officer shall, after considering the representation, if any, made by the person chargeable with tax, determine the amount of tax, interest and penalty due from such person and issue an order.

(3) Where any person chargeable with tax pays the amount of tax, interest and penalty determined under sub-section (2) within thirty days of the service of the order, no further proceedings shall be initiated against him in respect of the said tax.
        """.strip(),
    },
    {
        "title": "CGST Act, 2017 - Section 74 (Determination of tax not paid or short paid or erroneously refunded or input tax credit wrongly availed or utilised by reason of fraud)",
        "source_type": "act",
        "url": "https://www.gst.gov.in/legal/acts-rules",
        "version": "2017",
        "content": """
Section 74: Determination of tax not paid or short paid or erroneously refunded or input tax credit wrongly availed or utilised by reason of fraud.

(1) Where it appears to the proper officer that any tax has not been paid or short paid or erroneously refunded, or where input tax credit has been wrongly availed or utilised by reason of fraud or any wilful misstatement or suppression of facts to evade tax, he shall serve notice on the person chargeable with tax which has not been so paid or which has been so short paid or to whom the refund has erroneously been made, or who has wrongly availed or utilised input tax credit, requiring him to show cause as to why he should not pay the amount specified in the notice along with interest payable thereon under section 50 and a penalty equivalent to the tax.

(2) The proper officer shall, after considering the representation, if any, made by the person chargeable with tax, determine the amount of tax, interest and penalty due from such person and issue an order.

(3) Where any person chargeable with tax pays the amount of tax, interest and penalty determined under sub-section (2) within thirty days of the service of the order, no further proceedings shall be initiated against him in respect of the said tax.
        """.strip(),
    },
    {
        "title": "GST Circular No. 183/15/2022-GST - Clarification on ITC availment and reconciliation",
        "source_type": "circular",
        "url": "https://www.gst.gov.in/legal/circulars",
        "version": "2022",
        "content": """
Circular No. 183/15/2022-GST dated 13.10.2022

Subject: Clarification on issues related to Input Tax Credit (ITC) availment and reconciliation.

1. It has been brought to the notice of the Board that taxpayers are facing difficulties in reconciling their ITC as per books of accounts with the ITC available in GSTR-2B.

2. The Board clarifies that the ITC available in GSTR-2B is an auto-drafted statement based on the returns filed by the suppliers. The taxpayer should reconcile his books of accounts with GSTR-2B and take appropriate action.

3. If a supplier has not filed GSTR-1 or has filed it with errors, the ITC will not reflect in the recipient's GSTR-2B. In such cases, the recipient should communicate with the supplier to rectify the error.

4. The recipient can claim ITC on a provisional basis under Section 41 of the CGST Act, subject to the conditions specified therein.

5. It is clarified that mere non-appearance of an invoice in GSTR-2B does not automatically disqualify the ITC, provided the recipient has the tax invoice and the supplier has actually paid the tax.
        """.strip(),
    },
    {
        "title": "GST Circular No. 158/14/2021-GST - Procedure for filing of appeals",
        "source_type": "circular",
        "url": "https://www.gst.gov.in/legal/circulars",
        "version": "2021",
        "content": """
Circular No. 158/14/2021-GST dated 15.11.2021

Subject: Procedure for filing of appeals under GST.

1. This circular provides the procedure for filing appeals against orders passed under the CGST Act, 2017.

2. Appeals under Section 107 of the CGST Act shall be filed in Form GST APL-01 along with the required documents.

3. The appeal must be filed within three months from the date of communication of the order.

4. The appellate authority may condone delay up to one month if sufficient cause is shown.

5. The appeal shall be accompanied by a certified copy of the order appealed against and a statement of facts.
        """.strip(),
    },
    {
        "title": "Income Tax Act, 1961 - Section 148 (Reassessment)",
        "source_type": "act",
        "url": "https://www.incometax.gov.in/iec/foportal/acts",
        "version": "1961",
        "content": """
Section 148: Income escaping assessment.

If the Assessing Officer has reason to believe that any income chargeable to tax has escaped assessment for any assessment year, he may, subject to the provisions of sections 148A to 148D, assess or reassess such income and also any other income chargeable to tax which has escaped assessment and which comes to his notice subsequently in the course of the proceedings under this section, or recompute the loss or the depreciation allowance or any other deduction allowable under this Act for the assessment year concerned.

The Assessing Officer shall have reason to believe that any income chargeable to tax has escaped assessment where—
(a) there is information in his possession that any income chargeable to tax has escaped assessment; or
(b) the assessee has failed to file a return of income under section 139 and the Assessing Officer has reason to believe that the income of the assessee exceeds the maximum amount which is not chargeable to tax; or
(c) the assessee has filed a return of income but the Assessing Officer has reason to believe that any income chargeable to tax has escaped assessment.
        """.strip(),
    },
    {
        "title": "Income Tax Act, 1961 - Section 142(1) (Inquiry before assessment)",
        "source_type": "act",
        "url": "https://www.incometax.gov.in/iec/foportal/acts",
        "version": "1961",
        "content": """
Section 142(1): Inquiry before assessment.

For the purpose of making an assessment under this Chapter, the Assessing Officer may serve on any person who has made a return under section 139 or in whose case the time allowed for furnishing the return has expired, a notice requiring him, on a date and at a place to be specified therein,—
(a) to produce, or cause to be produced, such accounts or documents as the Assessing Officer may require; and
(b) to furnish in writing, and verified in the manner specified in the notice, such information as the Assessing Officer may require on any matter, including his own income and the income of any other person in respect of which he is assessable under this Act.
        """.strip(),
    },
    {
        "title": "GST FAQ - GSTR-2B Reconciliation",
        "source_type": "faq",
        "url": "https://tutorial.gst.gov.in/userguide/returns/FAQ_gstr2b.htm",
        "version": "2023",
        "content": """
GSTR-2B FAQ

Q1: What is GSTR-2B?
A: GSTR-2B is an auto-drafted Input Tax Credit (ITC) statement which is made available to every registered person on the GST portal on the basis of the returns filed by their suppliers.

Q2: How frequently is GSTR-2B generated?
A: GSTR-2B is generated on a monthly basis.

Q3: What should a taxpayer do if an invoice is missing in GSTR-2B?
A: If an invoice is missing in GSTR-2B, the taxpayer should contact the supplier and request them to file or amend their GSTR-1 return. The taxpayer should also check if the supplier has opted for QRMP scheme.

Q4: Can I claim ITC on invoices not appearing in GSTR-2B?
A: ITC can be claimed on a provisional basis subject to the conditions of Section 16(2) of CGST Act. However, the taxpayer should make efforts to get the supplier to upload the invoice.

Q5: What is the difference between GSTR-2A and GSTR-2B?
A: GSTR-2A is a dynamic statement that updates in real-time as suppliers file their returns. GSTR-2B is a static statement generated on the 14th of the succeeding month.
        """.strip(),
    },
]


def main():
    """Seed the knowledge base."""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    
    db = next(get_db())
    
    try:
        for source in OFFICIAL_SOURCES:
            print(f"Ingesting: {source['title'][:60]}...")
            result = ingest_official_source(
                db,
                tenant_id="seed_firm",  # Global tenant for official sources
                title=source["title"],
                source_type=source["source_type"],
                raw_text=source["content"],
                url=source["url"],
                version=source["version"],
            )
            print(f"  -> Ingested {result.id} with {len(result.chunks) if hasattr(result, 'chunks') else 'N/A'} chunks")
        
        print("\nKnowledge base seeding completed!")
        
    except Exception as e:
        print(f"Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()