import streamlit as st
import pandas as pd
import requests
from playwright.sync_api import sync_playwright
import zipfile
import io

def is_pdf(url):
    """Kontrollerar om URL:en pekar på en PDF-fil."""
    try:
        response = requests.head(url, allow_redirects=True, timeout=5)
        content_type = response.headers.get('content-type', '')
        if 'application/pdf' in content_type.lower():
            return True
    except Exception as e:
        print(f"Error checking if URL is PDF: {e}")
    return False

def download_pdf(url):
    """Laddar ner PDF-filen från URL:en."""
    try:
        response = requests.get(url, timeout=20)
        if response.status_code == 200:
            return response.content
    except Exception as e:
        print(f"Error downloading PDF from {url}: {e}")
    return None

def webpage_to_pdf(url):
    """Konverterar webbsidan till PDF med Playwright."""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(url, wait_until='networkidle', timeout=60000)
            pdf_content = page.pdf(format='A4')
            browser.close()
            return pdf_content
    except Exception as e:
        print(f"Error converting {url} to PDF: {e}")
        return None

st.title("URL till PDF Konverterare")

# Filuppladdning
uploaded_file = st.file_uploader("Ladda upp en Excel-fil med URL:er", type=["xlsx"])

if uploaded_file is not None:
    # Läser Excel-filen
    df = pd.read_excel(uploaded_file)
    st.write("## Innehåll i Excel-filen:")
    st.dataframe(df)

    # Antar att URL:erna finns i den första kolumnen
    # Tar bort NaN-värden, konverterar till strängar och tar bort tomma strängar
    urls = df.iloc[:, 0].dropna().astype(str).str.strip()
    urls = urls[urls != ''].tolist()

    pdf_files = []
    failed_urls = []  # Lista för misslyckade URL:er

    for idx, url in enumerate(urls):
        st.write(f"### Bearbetar URL {idx + 1}: {url}")

        if is_pdf(url):
            st.info("Detta är en PDF. Laddar ner...")
            pdf_content = download_pdf(url)
            if pdf_content:
                file_name = url.split('/')[-1] or f"document_{idx + 1}.pdf"
                pdf_files.append((file_name, pdf_content))
                st.success(f"PDF {file_name} laddades ner.")
            else:
                st.error("Misslyckades med att ladda ner PDF.")
                failed_urls.append(url)  # Lägg till misslyckad URL
        else:
            st.info("Detta är en webbsida. Konverterar till PDF...")
            pdf_content = webpage_to_pdf(url)
            if pdf_content:
                file_name = f"webpage_{idx + 1}.pdf"
                pdf_files.append((file_name, pdf_content))
                st.success(f"Webbsidan konverterades till {file_name}.")
            else:
                st.error("Misslyckades med att konvertera webbsidan till PDF.")
                failed_urls.append(url)  # Lägg till misslyckad URL

    if pdf_files or failed_urls:
        # Skapar en ZIP-fil i minnet
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
            # Lägg till PDF-filer i ZIP
            for file_name, data in pdf_files:
                zip_file.writestr(file_name, data)
            # Lägg till Excel-fil med misslyckade URL:er om det finns några
            if failed_urls:
                failed_df = pd.DataFrame(failed_urls, columns=['URL'])
                excel_buffer = io.BytesIO()
                with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                    failed_df.to_excel(writer, index=False)
                excel_buffer.seek(0)
                zip_file.writestr('misslyckade_urler.xlsx', excel_buffer.read())
        zip_buffer.seek(0)

        st.download_button(
            label="Ladda ner PDF-filer (och misslyckade URL:er) som ZIP",
            data=zip_buffer,
            file_name='pdf_files.zip',
            mime='application/zip'
        )
    else:
        st.warning("Inga PDF-filer att ladda ner.")
