import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

# ==============================================================================
# ===== CONFIGURATION ==========================================================
# ==============================================================================
# La ruta donde están tus archivos de Excel y donde se guardará el dashboard.
FILES_PATH = "/Users/User/Desktop"

ANNOTATOR_FILES = {
    "Gonzalo": "First 12 annotations - Gonzalo Soto.xlsx",
    "Jose Luis": "First 12 annotations JoselLuis.xlsx",
    "Julio": "First 12 annotations_Julio.xlsx",
    "Rodrigo": "First 12 annotations rodrigo.xlsx",
    "Rafa": "First 12 annotations Rafael Almarcha.xlsx"
}
# ==============================================================================

def load_and_align_annotations(filepath, annotator_name):
    """Loads and aligns plays from a single Excel file."""
    try:
        df = pd.read_excel(filepath)
        print(f"✅ Archivo Excel '{os.path.basename(filepath)}' cargado para {annotator_name}.")
        player_col = 'Nº Player '
        if player_col not in df.columns: return None
        first_valid_row = df[player_col].first_valid_index()
        if first_valid_row is None: return None
        df = df.loc[first_valid_row:].reset_index(drop=True)
        is_separator = df.isnull().all(axis=1)
        is_new_play = (is_separator.shift(1).fillna(True)) & (~is_separator)
        df['Aligned_Index'] = is_new_play.cumsum() - 1 
        df.dropna(how='all', inplace=True)
        df.dropna(subset=[player_col], inplace=True)
        df['Annotator'] = annotator_name
        df = df.rename(columns={player_col: 'Nº Player'})
        return df
    except Exception as e:
        print(f"--- ❌ ERROR reading file for {annotator_name}: {e} ---")
        return None

# --- Main Execution ---
print("Starting Final Annotator Analysis...")
print(f"Los archivos se leerán de: '{FILES_PATH}'")

all_dfs = []
for name, filename in ANNOTATOR_FILES.items():
    full_path = os.path.join(FILES_PATH, filename)
    processed_df = load_and_align_annotations(full_path, name)
    if processed_df is not None:
        all_dfs.append(processed_df)

if not all_dfs:
    print("\n--- 🛑 CRITICAL ERROR: No data could be loaded. Aborting script. ---")
else:
    df = pd.concat(all_dfs, ignore_index=True)
    df = df.astype({'Nº Player': 'int', 'Aligned_Index': 'int'})
    print("\n--- ✅ Data loaded. Generating final 6-panel dashboard... ---")

    # Prepare columns for analysis
    ANALYSIS_COLS = ['Defender Type', 'Defender Behaviours', 'Behavior Outcomes']
    BOOL_COLS = ['Aware of the Run', 'Multiple Responsabilities']
    for col in ANALYSIS_COLS + BOOL_COLS:
        if col not in df.columns: df[col] = 'N/A'
        if col in BOOL_COLS:
            df[col] = df[col].replace({1: True, 0: False, '1': True, '0': False})
        df[col] = df[col].astype(str)

    # Data Preparation for each Panel
    disagreement_matrix = df.groupby('Aligned_Index')[ANALYSIS_COLS].nunique()
    behav_usage_crosstab = pd.crosstab(df['Annotator'], df['Defender Behaviours'])
    outcomes_usage_crosstab = pd.crosstab(df['Annotator'], df['Behavior Outcomes'])
    aware_crosstab = pd.crosstab(df['Annotator'], df['Aware of the Run'], normalize='index') * 100
    resp_crosstab = pd.crosstab(df['Annotator'], df['Multiple Responsabilities'], normalize='index') * 100

    # --- Dashboard Visualization (3x2 Grid) ---
    fig, axes = plt.subplots(3, 2, figsize=(22, 27))
    fig.patch.set_facecolor('#F8F9FA')

    # Panel 1
    ax1 = axes[0, 0]
    sns.countplot(y='Annotator', data=df, ax=ax1, palette='viridis', order=df['Annotator'].value_counts().index)
    ax1.set_title('1. Total Annotations by Analyst', fontsize=16, weight='bold', loc='left')

    # Panel 2
    ax2 = axes[0, 1]
    sns.heatmap(disagreement_matrix, annot=True, cmap='rocket_r', fmt='d', linewidths=.5, ax=ax2, cbar=False)
    ax2.set_title('2. Disagreement Heatmap per Play', fontsize=16, weight='bold', loc='left')

    # Panel 3
    ax3 = axes[1, 0]
    sns.heatmap(behav_usage_crosstab, annot=True, cmap='Blues', fmt='d', linewidths=.5, ax=ax3, cbar=False)
    ax3.set_title('3. \'Defender Behaviours\' Usage Frequency', fontsize=16, weight='bold', loc='left')

    # Panel 4
    ax4 = axes[1, 1]
    sns.heatmap(outcomes_usage_crosstab, annot=True, cmap='Greens', fmt='d', linewidths=.5, ax=ax4, cbar=False)
    ax4.set_title('4. \'Behavior Outcomes\' Usage Frequency', fontsize=16, weight='bold', loc='left')

    # Panel 5
    ax5 = axes[2, 0]
    if 'True' not in aware_crosstab.columns: aware_crosstab['True'] = 0
    if 'False' not in aware_crosstab.columns: aware_crosstab['False'] = 0
    aware_crosstab[['True', 'False']].plot(kind='barh', stacked=True, ax=ax5, colormap='coolwarm_r', legend=True)
    ax5.set_title('5. Agreement on "Aware of the Run"', fontsize=16, weight='bold', loc='left')

    # Panel 6
    ax6 = axes[2, 1]
    if 'True' not in resp_crosstab.columns: resp_crosstab['True'] = 0
    if 'False' not in resp_crosstab.columns: resp_crosstab['False'] = 0
    resp_crosstab[['True', 'False']].plot(kind='barh', stacked=True, ax=ax6, colormap='coolwarm_r', legend=True)
    ax6.set_title('6. Agreement on "Multiple Responsabilities"', fontsize=16, weight='bold', loc='left')
    
    # Overall Title and Layout
    fig.suptitle('Final Annotator Analysis Dashboard', fontsize=24, weight='bold')
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    
    # --- CAMBIO CLAVE: Guardar en la misma carpeta que los Excel ---
    dashboard_path = os.path.join(FILES_PATH, 'Final_Dashboard.png')
    plt.savefig(dashboard_path, dpi=300, facecolor=fig.get_facecolor())
    
    print(f"\n--- ✅ ¡Análisis completo! El dashboard se ha guardado en: '{dashboard_path}' ---")