from pathlib import Path
import argparse
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from src.data_io import load_all
from src.rainfall import Region, CropRule, MONTHS, comparison_matrices

BASE=Path(__file__).resolve().parent
RAW=BASE/'data'/'raw'
OUT=BASE/'data'/'processed'
FIG=BASE/'figures'
for folder in [RAW,OUT,FIG]: folder.mkdir(parents=True,exist_ok=True)

# Uganda MAAIF maize preference; FAO seasonal water needs for other crops.
# Approximate 4/3/4 months are modelling assumptions, not official variety durations.
CROPS=[
    CropRule('Maize',500,600,4,'Uganda MAAIF maize extension manual'),
    CropRule('Beans',300,500,3,'FAO crop water needs; MAAIF beans manual'),
    CropRule('Groundnuts',500,700,4,'FAO crop water needs')
]

def analyse(offline=False):
    daily,monthly=load_all(RAW,offline=offline)
    monthly.to_csv(OUT/'monthly_rainfall_2015_2024.csv',index=False)
    climatology=monthly.groupby(['region','month'],as_index=False).rainfall_mm.mean()
    climatology.to_csv(OUT/'monthly_climatology.csv',index=False)
    regions={name:Region(name,climatology.loc[climatology.region.eq(name)]
                         .sort_values('month').rainfall_mm.to_numpy())
             for name in ['Kampala','Gulu','Mbarara']}
    summary=pd.DataFrame([dict(region=r.name,mean_annual_mm=r.annual_total(),
                mean_monthly_mm=r.mean(),cv=r.cv(),wettest=r.wettest_month(),
                driest=r.driest_month(),peaks=','.join(MONTHS[i] for i in r.rainy_peaks()),
                season_pattern=r.season_pattern()) for r in regions.values()])
    summary.to_csv(OUT/'regional_summary.csv',index=False)
    print('\nREGIONAL SUMMARY (10-year monthly climatology)\n',summary.to_string(index=False))

    names,matrices=comparison_matrices(regions)
    for metric,arr in matrices.items():
        matrix=pd.DataFrame(arr,index=names,columns=names)
        matrix.to_csv(OUT/f'{metric}_matrix.csv')
        print('\n',metric,'\n',matrix.round(3))

    # Assignment monthly classification: seasonal requirement divided by assumed months.
    monthly_rows=[]
    for region,r in regions.items():
        for month,mm in enumerate(r.rainfall,1):
            for crop in CROPS:
                lower=crop.min_mm/crop.growing_months
                upper=crop.max_mm/crop.growing_months
                label='Below reference' if mm<lower else ('Within reference' if mm<=upper else 'Above reference')
                monthly_rows.append(dict(region=region,month=month,crop=crop.name,
                    rainfall_mm=mm,reference_min_mm=lower,reference_max_mm=upper,
                    classification=label))
    month_df=pd.DataFrame(monthly_rows)
    month_df.to_csv(OUT/'monthly_crop_classification.csv',index=False)

    # Better seasonal comparison: observed total rainfall in successive months,
    # with calendar wraparound for planting in November/December.
    rows=[]
    for region,r in regions.items():
        for crop in CROPS:
            for start in range(12):
                months=[(start+j)%12 for j in range(crop.growing_months)]
                total=float(r.rainfall[months].sum())
                label=crop.classify(total)
                rows.append(dict(region=region,crop=crop.name,planting_month=MONTHS[start],
                    growing_months=crop.growing_months,rainfall_total_mm=total,
                    min_reference_mm=crop.min_mm,max_reference_mm=crop.max_mm,
                    classification=label))
    seasonal=pd.DataFrame(rows)
    seasonal.to_csv(OUT/'seasonal_crop_suitability.csv',index=False)

    fig,ax=plt.subplots(figsize=(11,5))
    for r in regions.values(): ax.plot(MONTHS,r.rainfall,marker='o',label=r.name)
    ax.set(title='NASA POWER mean monthly rainfall, Uganda (2015–2024)',
           xlabel='Month',ylabel='Rainfall (mm)')
    ax.legend();ax.grid(alpha=.3);fig.tight_layout()
    fig.savefig(FIG/'rainfall_lines.png',dpi=160);plt.close(fig)

    fig,ax=plt.subplots(figsize=(11,5))
    positions=[];values=[];labels=[]
    for m in range(1,13):
        for i,region in enumerate(regions):
            vals=monthly.loc[(monthly.month==m)&(monthly.region==region),'rainfall_mm']
            positions.append(m+(i-1)*.22);values.append(vals.to_numpy())
    box=ax.boxplot(values,positions=positions,widths=.18,patch_artist=True,manage_ticks=False)
    ax.set_xticks(range(1,13),MONTHS)
    ax.set(xlabel='Month',ylabel='Monthly total (mm)',
           title='Year-to-year monthly rainfall variability, 2015–2024')
    ax.grid(axis='y',alpha=.2);fig.tight_layout()
    fig.savefig(FIG/'rainfall_boxplots.png',dpi=160);plt.close(fig)

    # One heatmap with all three crops: rows are region/crop, columns planting month.
    codes={'Below reference':0,'Within reference':1,'Above reference':2}
    h=seasonal.assign(code=seasonal.classification.map(codes),
        row=seasonal.region+' – '+seasonal.crop)
    pivot=h.pivot(index='row',columns='planting_month',values='code').reindex(columns=MONTHS)
    fig,ax=plt.subplots(figsize=(12,6))
    im=ax.imshow(pivot.to_numpy(),aspect='auto',vmin=0,vmax=2,cmap='YlGnBu')
    ax.set_xticks(range(12),MONTHS)
    ax.set_yticks(range(len(pivot)),pivot.index)
    ax.set(title='Seasonal rainfall reference by planting month (10-year averages)',
           xlabel='Planting month')
    cb=fig.colorbar(im,ax=ax,ticks=[0,1,2])
    cb.ax.set_yticklabels(['Below','Within','Above'])
    fig.tight_layout();fig.savefig(FIG/'crop_heatmap.png',dpi=160);plt.close(fig)

    print('\nSaved CSV results to',OUT)
    print('Saved charts to',FIG)
    return dict(daily=daily,monthly=monthly,regions=regions,crops=CROPS,
                names=names,matrices=matrices,seasonal=seasonal,monthly_classification=month_df,
                summary=summary)

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--offline',action='store_true',help='Use downloaded NASA files only')
    args=parser.parse_args()
    analyse(offline=args.offline)
