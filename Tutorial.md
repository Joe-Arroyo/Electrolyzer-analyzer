# Tutorial
## **File formats:**
   pyEAT reads raw data files directly from the instrument software or from exported files, it handles the parsing automatically for each tab. 
   - GAMRY (.DTA): file exported directly from Gamry Framework during the experiment. The Gamry parser reads the file directly with no need for external libraries or dependencies. According to the experiment, the data used by pyEAT:

      | Column | Description |
      |---|---|
      | `T` | Time (seconds) |
      | `Vf` | Voltage vs. reference (V) |
      | `Im` | Current (A) |
      | `Freq` | Frequency (Hz) — EIS only |
      | `Zreal` | Real impedance (Ω) — EIS only |
      | `Zimag` | Imaginary impedance (Ω) — EIS only |

       - pyEAT supports both US (.) and European (,) decimal formats automatically
            
   - AUTOLAB (.xlsx, .txt): pyEAT does not open .NOX files so it reads exported files from the Autolab NOVA Software with semicolon-separated (;) columns with comma as decimal separator. One header row with column names and data below.
     
      For EIS:
     
      | Column | Description |
      |---|---|
      | `Frequency` | Frequency (Hz) |
      | `Z'` | Real impedance (Ω) |
      | `-Z''` | Negative imaginary impedance (Ω) |
     
     Note: Autolab exports -Z'' (negative imaginary). pyEAT automatically negates it internally to follow the standard convention.

      For polarization curves and chronopotentiometry it uses the same parser and read the same data:

      | Column | Description |
      |---|---|
      | `Time (s)` | Time (seconds) |
      | `WE(1).Potential (V)` | Voltage vs. reference (V) |
      | `WE(1).Current (A)` | Current (A) |

    
      - The parser tries both tab (\t) and semicolon (;) separators automatically
      - Column names are matched by keyword, not exact name — so minor variations in NOVA's export format are handled and no particular order for the columns in the datafile.
            
   - RIDEN (.xlsx): this file comes from the Riden power supplies (RD 6006 for our case) as an standard exce; file.
     
      | Column | Description |
      |---|---|
      | `Read Time` | Timestamp (HH:MM:SS) |
      | `Output Voltage` | Voltage (V) |
      | `Output Current` | Current (A) |

      - Only supported for chronopotentiometry and polarization curves — not EIS
      - One .xlsx file can contain a full multi-step chronopotentiometry experiment
      - Parser matches by keywords not by column order
      - **Caution:** some stored values are stored as text and will not work with pyEAT. Convert these values into numbers in Excel or similar, here is an example:
        
        <img width="521" height="239" alt="image" src="https://github.com/user-attachments/assets/337467d8-566f-45ad-b50a-d09bdbb02420" />

   - Custom CSV (.txt): designed for custom powwer supplies, this is the most strict format since it takes the values from column order, no keywords.
     
      | Position | Column | Description |
      |---|---|---|
      | 1 | `voltage` | Voltage (V) |
      | 2 | `current` | Current (A) |
      | 3 | `power` | Power (W) |
      | 4 | `timestamp` | Date and time (`DD/MM/YYYY HH:MM:SS`) |

      - No header row — the first line must be data
      - Comma-separated
      - Timestamp format must be exactly DD/MM/YYYY HH:MM:SS
      - Only supported for chronopotentiometry and polarization curves — not EIS

      **Future versions will be more flexible in terms of column order and time format**

     
## **How to use pyEAT**     
1. EIS tab
2. Polarization curve tab
3. Chronopotentiometry tab
