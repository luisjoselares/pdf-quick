import io
import re

import pandas as pd
import pdfplumber


class ExcelController:
    """Conversión de PDF a Excel usando pdfplumber y pandas.

    Detecta tablas a partir de bordes ('lines') y estructuras de texto
    ('text'), limpia celdas de saltos de línea y genera un archivo
    .xlsx en memoria.
    """

    @staticmethod
    def pdf_to_excel(file, strategies=("lines", "text")):
        file.seek(0)
        pdf = pdfplumber.open(io.BytesIO(file.read()))
        output = io.BytesIO()

        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            sheet_names = []
            table_count = 0

            for page_index, page in enumerate(pdf.pages, start=1):
                tables = ExcelController._extract_tables(page, strategies)
                for table_index, table in enumerate(tables, start=1):
                    df = ExcelController._build_dataframe(table)
                    sheet_name = ExcelController._format_sheet_name(
                        page_index, table_index, sheet_names
                    )
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
                    sheet_names.append(sheet_name)
                    table_count += 1

            if table_count == 0:
                raise ValueError("No se encontraron tablas estructuradas en el PDF.")

            writer.save()

        output.seek(0)
        return output, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "convertido.xlsx"

    @staticmethod
    def _extract_tables(page, strategies):
        tables = []
        seen = set()

        for strategy in strategies:
            settings = {
                "vertical_strategy": strategy,
                "horizontal_strategy": strategy,
                "intersection_tolerance": 5,
                "snap_tolerance": 3,
                "join_tolerance": 3,
            }
            extracted = page.extract_tables(table_settings=settings) or []
            for table in extracted:
                normalized = ExcelController._normalize_table(table)
                if not normalized:
                    continue
                key = tuple(tuple(cell or "" for cell in row) for row in normalized)
                if key in seen:
                    continue
                seen.add(key)
                tables.append(normalized)

        return tables

    @staticmethod
    def _normalize_table(table):
        normalized = []
        for row in table:
            if not any(cell is not None and str(cell).strip() for cell in row):
                continue
            normalized.append([cell if cell is not None else "" for cell in row])
        return normalized

    @staticmethod
    def _build_dataframe(table):
        rows = [
            [ExcelController._clean_cell(cell) for cell in row]
            for row in table
        ]
        if ExcelController._looks_like_header(rows):
            header = rows[0]
            data = rows[1:]
            return pd.DataFrame(data, columns=header)
        return pd.DataFrame(rows)

    @staticmethod
    def _looks_like_header(rows):
        if len(rows) < 2:
            return False

        first = rows[0]
        second = rows[1]
        if not any(cell.strip() for cell in first if isinstance(cell, str)):
            return False

        if all(ExcelController._is_numeric(cell) for cell in first if cell != ""):
            return False

        first_has_text = sum(
            1 for cell in first if isinstance(cell, str) and re.search(r"[A-Za-z]", cell)
        )
        second_has_text = sum(
            1 for cell in second if isinstance(cell, str) and re.search(r"[A-Za-z]", cell)
        )
        second_has_numbers = any(ExcelController._is_numeric(cell) for cell in second)

        if first_has_text and second_has_numbers:
            return True

        if first_has_text > 0 and first_has_text >= second_has_text:
            return True

        return False

    @staticmethod
    def _is_numeric(value):
        if value is None:
            return False
        text = str(value).strip().replace("%", "")
        if not text:
            return False
        try:
            float(text.replace(",", "."))
            return True
        except ValueError:
            return False

    @staticmethod
    def _clean_cell(cell):
        if cell is None:
            return ""
        return str(cell).replace("\n", " ").strip()

    @staticmethod
    def _format_sheet_name(page_index, table_index, existing_names):
        base = f"Page{page_index}_Table{table_index}"
        name = base[:31]
        suffix = 1
        while name in existing_names:
            available = 31 - len(str(suffix))
            name = f"{base[:available]}{suffix}"
            suffix += 1
        return name
