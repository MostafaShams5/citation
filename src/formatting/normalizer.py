import re

class CitationNormalizer:
    """
    Final Post-Processing Layer.
    Uses highly targeted pattern matching to resolve specific CSL engine
    tokenizer errors and enforce consistent academic punctuation.
    """
    
    @staticmethod
    def normalize(text: str, style: str = "", is_preprint: bool = False) -> str:
        if not text:
            return ""

        # ==========================================
        # 1. PUBLISHER STANDARDIZATION
        # ==========================================
        # APA and Chicago prefer "Qeios" over the legal entity "Qeios Ltd"
        text = text.replace("Qeios Ltd", "Qeios")

        # ==========================================
        # 2. THE APOSTROPHE FIX
        # ==========================================
        text = text.replace("’ s ", "’s ")
        text = text.replace("' s ", "'s ")
        text = re.sub(r"([a-zA-Z])\s*['’‘]\s*([a-zA-Z])", r"\1’\2", text)

        # ==========================================
        # 3. QUOTATION MARK BOUNDARIES
        # ==========================================
        text = re.sub(r'([a-zA-Z])([”"])\.', r'\1.\2', text)
        text = re.sub(r'([a-zA-Z])([”"]),', r'\1,\2', text)
        text = re.sub(r'([a-zA-Z])([”"])\s*([A-Z])', r'\1.\2 \3', text)

        # ==========================================
        # 4. CHICAGO STYLE SPECIFICS
        # ==========================================
        if "Chicago" in style:
            # [NEW] Enforce Oxford comma before 'and' (e.g., "Aucott and" -> "Aucott, and")
            text = re.sub(r'([a-zA-Z])\s+and\s+([A-Z])', r'\1, and \2', text)
            
            # [NEW] Enforce period before Year (e.g., "Mon-Williams 2016" -> "Mon-Williams. 2016")
            text = re.sub(r'([a-zA-Z])\s+(19\d{2}|20\d{2})(?!\d)', r'\1. \2', text)
            
            # Enforce period after Year (e.g., "2016 Moving" -> "2016. Moving")
            text = re.sub(r'(19\d{2}|20\d{2})\s*([A-Za-z“"‘\'])', r'\1. \2', text)
            
            # Enforce space before issue number (e.g., "11(7)" -> "11 (7)")
            text = re.sub(r'(\d+)\((\d+)\):', r'\1 (\2):', text)
            
            # Chicago Preprint tagging
            if is_preprint:
                text = re.sub(r'(\bQeios\b)', r'Preprint, \1', text)

        # ==========================================
        # 5. MLA FORMATTING RULES
        # ==========================================
        if "MLA" in style:
            # [NEW] Strip "p." abbreviation for electronic article numbers
            text = re.sub(r'\bp\.\s+(e\d+)', r'\1', text)

        # ==========================================
        # 6. IEEE FORMATTING RULES
        # ==========================================
        if "IEEE" in style:
            # Convert 'p.' to 'Art. no.' for electronic article numbers
            text = re.sub(r'\bp\.\s+(e\d+)', r'Art. no. \1', text)

        # ==========================================
        # 7. APA FORMATTING RULES
        # ==========================================
        if "APA" in style:
            # APA Preprint tagging
            if is_preprint:
                text = re.sub(r'(\.)(\s*Qeios)', r' [Preprint]\1\2', text)

        # ==========================================
        # 8. SQUASHED CONJUNCTIONS & BRACKETS
        # ==========================================
        text = re.sub(r'([A-Za-z\.])and\s', r'\1 and ', text)
        text = re.sub(r'([A-Za-z\.])&', r'\1 &', text)
        text = re.sub(r'(\[\d+\])([A-Za-z])', r'\1 \2', text)

        # ==========================================
        # 9. URL & DOI SPACING
        # ==========================================
        text = re.sub(r'([A-Za-z0-9\.])(https?://)', r'\1 \2', text)

        # ==========================================
        # 10. CSL ARTIFACT CLEANUP
        # ==========================================
        text = re.sub(r'Edition\.', '.', text)
        text = re.sub(r',\s*ahead of print', '', text)

        # ==========================================
        # 11. FINAL PUNCTUATION CONSOLIDATION
        # ==========================================
        text = re.sub(r'\.\.+', '.', text)
        text = re.sub(r'\s+,', ',', text)
        text = re.sub(r'\s+\.', '.', text)
        text = text.replace("..", ".")

        # ==========================================
        # 12. DOI INTEGRITY PROTECTION
        # ==========================================
        text = re.sub(r'(10\.)\s+(\d{4,9})', r'\1\2', text)

        return text.strip()
