import pyodbc
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from dotenv import load_dotenv
import os

# Załaduj zmienne środowiskowe z pliku .env
load_dotenv()

# Parametry połączenia
dsn = 'RekordES'

# Pobierz dane logowania
login = os.getenv("MY_LOGIN")
password = os.getenv("MY_PASSWORD")





# Funkcja do pobierania unikalnych wartości do filtrów
@st.cache_data
def get_unique_values(column_name):
    try:
        conn = pyodbc.connect(f'DSN={dsn};UID={login};PWD={password}')
        cursor = conn.cursor()
        query = f"SELECT DISTINCT {column_name} FROM M_OPERBRAKI WHERE {column_name} IS NOT NULL ORDER BY {column_name}"
        cursor.execute(query)
        values = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        return values
    except pyodbc.Error as e:
        st.error(f"❌ Błąd pobierania wartości dla {column_name}: {e}")
        return []

# Funkcja do pobierania danych z bazy danych
def get_data(years, KAT_ZLEC=None, SYMBOL_OBJ=None):
    try:
        conn = pyodbc.connect(f'DSN={dsn};UID={login};PWD={password}')
        cursor = conn.cursor()

        # Budujemy warunki WHERE
        conditions = []
        params = []

        if years:
            placeholders = ','.join(['?'] * len(years))
            conditions.append(f"B.ROK_OBL IN ({placeholders})")
            params.extend(years)

        if KAT_ZLEC:
            placeholders = ','.join(['?'] * len(KAT_ZLEC))
            conditions.append(f"B.KAT_ZLEC IN ({placeholders})")
            params.extend(KAT_ZLEC)

        if SYMBOL_OBJ:
            placeholders = ','.join(['?'] * len(SYMBOL_OBJ))
            conditions.append(f"B.SYMBOL_OBJ IN ({placeholders})")
            params.extend(SYMBOL_OBJ)

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        query = f'''
            SELECT B.ROK_OBL, B.NUMER, B.KAT_ZLEC, B.SYMB_ZLEC, B.LP_ZLEC, B.NR_PRZEW, 
                   B.DATA_REJ, B.SYMBOL_OBJ, B.PRZYCZYNA, B.OPIS, B.SR_ZARADCZE, 
                   B.MIEJSCE_POWST, MPB.NAZWA, B.NUM_PRZEWOD, B.INDEKS, B.IDENT 
            FROM M_OPERBRAKI B 
            LEFT JOIN M_MP_BRAKOW MPB ON MPB.SYMBOL = B.MIEJSCE_POWST 
            WHERE {where_clause}
            ORDER BY ROK_OBL DESC, NUMER DESC
        '''
        cursor.execute(query, params)
        columns = [column[0] for column in cursor.description]
        data = cursor.fetchall()
        df = pd.DataFrame.from_records(data, columns=columns)
        cursor.close()
        conn.close()
        return df

    except pyodbc.Error as e:
        st.error(f"❌ Błąd połączenia z bazą danych: {e}")
        return None

# Funkcja do generowania wykresu
def plot_data(df):
    plt.figure(figsize=(10, 6))
    ax = df.groupby('ROK_OBL')['NUMER'].count().sort_index().plot(kind='bar', color='skyblue')
    plt.title('Liczba zgłoszeń w podziale na lata')
    plt.xlabel('Rok')
    plt.ylabel('Liczba zgłoszeń')
    plt.xticks(rotation=45)
    plt.tight_layout()
    for p in ax.patches:
        height = p.get_height()
        ax.annotate(f'{int(height)}', 
                    (p.get_x() + p.get_width() / 2, height), 
                    ha='center', va='bottom')
    st.pyplot(plt)

# Interfejs użytkownika
st.sidebar.title("📂 Menu")
page = st.sidebar.radio("Wybierz widok:", ["📊 Wykresy", "📁 Tabela", "⚙️ Ustawienia"])

# Wspólne filtry
selected_years = st.multiselect("Wybierz lata", options=list(range(2020, 2030)), default=[2023, 2024, 2025])

kat_zlec_options = get_unique_values("KAT_ZLEC")
KAT_ZLEC = st.multiselect("Filtr: Kategoria zlecenia (KAT_ZLEC)", options=kat_zlec_options)

symbol_obj_options = get_unique_values("SYMBOL_OBJ")
SYMBOL_OBJ = st.multiselect("Filtr: Kategoria niezgodności (SYMBOL_OBJ)", options=symbol_obj_options)

# Widoki
if page == "📊 Wykresy":
    st.header("📊 Wykresy")
    if selected_years:
        data = get_data(selected_years, KAT_ZLEC or None, SYMBOL_OBJ or None)
        if data is not None and not data.empty:
            plot_data(data)
        else:
            st.warning("Brak danych dla wybranych filtrów.")
    else:
        st.info("Wybierz lata, aby wygenerować wykres.")

elif page == "📁 Tabela":
    st.header("📁 Tabela danych")
    if selected_years:
        data = get_data(selected_years, KAT_ZLEC or None, SYMBOL_OBJ or None)
        if data is not None and not data.empty:
            st.dataframe(data)
        else:
            st.warning("Brak danych dla wybranych filtrów.")
    else:
        st.info("Wybierz lata, aby wyświetlić tabelę.")

elif page == "⚙️ Ustawienia":
    st.header("⚙️ Ustawienia")
    st.write("Tutaj będą ustawienia...")
