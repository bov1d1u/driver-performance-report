import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from datetime import datetime

pd.set_option('display.max_columns', None, 'display.width', 200)

# Load and prepare data
df = pd.read_csv("deliveries.csv")
df[["start_time", "end_time"]] = df[["start_time", "end_time"]].apply(pd.to_datetime)
df["duration_minutes"] = (df["end_time"] - df["start_time"]).dt.total_seconds() / 60

# Calculate driver metrics
driver_group = df.groupby("driver")
fuel_eff = (driver_group["distance_km"].sum() / driver_group["fuel_liters"].sum() 
            if "fuel_liters" in df.columns else pd.Series(index=driver_group.size().index, dtype=float))

report = pd.DataFrame({
    "Total Deliveries": driver_group["delivery_id"].count(),
    "Average Delay (min)": driver_group["delay_minutes"].mean().round(2),
    "Total Distance (km)": driver_group["distance_km"].sum(),
    "Fuel Efficiency (km/l)": fuel_eff.round(2),
    "On-Time Delivery %": driver_group.apply(lambda x: (x["delay_minutes"] == 0).mean() * 100).round(1)
})

print(report)

# Find top 3 best drivers (lowest delay, highest on-time %)
report["Score"] = (100 - report["Average Delay (min)"]) + report["On-Time Delivery %"]
top_3 = report.nlargest(3, "Score")

# Display top 3 drivers popup
fig, ax = plt.subplots(figsize=(10, 6))
ax.axis('tight')
ax.axis('off')
table = ax.table(
    cellText=top_3.drop("Score", axis=1).round(2).values,
    colLabels=top_3.drop("Score", axis=1).columns,
    rowLabels=top_3.index,
    cellLoc='center',
    loc='center'
)
table.auto_set_font_size(False)
table.set_fontsize(11)
table.scale(1, 2)
plt.title("Top 3 Best Drivers - Today", fontsize=16, fontweight='bold', pad=20)
plt.show()
plt.close()

# Generate PDF report (no popups)
today = datetime.now().strftime("%Y-%m-%d")
pdf_filename = f"Driver_Performance_Report_{today}.pdf"

with PdfPages(pdf_filename) as pdf:
    # Summary table
    fig, ax = plt.subplots(figsize=(11, 8))
    ax.axis('off')
    table = ax.table(cellText=report.drop("Score", axis=1).values, colLabels=report.drop("Score", axis=1).columns, rowLabels=report.index,
                     cellLoc='center', loc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 2.5)
    plt.title("Driver Performance Summary Report", fontsize=16, fontweight='bold', pad=20)
    pdf.savefig(fig, bbox_inches='tight')
    plt.close()

    # Charts
    charts = [
        ("Total Deliveries", "Number of Deliveries", 'steelblue'),
        ("Average Delay (min)", "Delay (minutes)", 'orange'),
        ("Fuel Efficiency (km/l)", "km per liter", 'green'),
        ("On-Time Delivery %", "On-Time %", 'purple'),
    ]
    
    for col, ylabel, color in charts:
        fig, ax = plt.subplots(figsize=(10, 6))
        report[col].plot(kind="bar", ax=ax, color=color)
        ax.set_title(f"{col} per Driver", fontsize=14, fontweight='bold')
        ax.set_xlabel("Driver")
        ax.set_ylabel(ylabel)
        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()

print(f"\n✓ PDF report saved: {pdf_filename}")
report.drop("Score", axis=1).to_csv(f"driver_report_{today}.csv")
print(f"✓ CSV report saved: driver_report_{today}.csv")

