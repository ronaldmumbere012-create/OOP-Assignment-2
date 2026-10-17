"""Run with: streamlit run app.py"""
from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st
from src.engine import (CourtRepository,PerformanceAnalyzer,ForecastService,
                        LinearForecaster,LastValueForecaster,DataValidationError)

st.set_page_config(page_title='Court Performance Analytics',page_icon='⚖️',layout='wide')
st.title('⚖️ Judiciary Case Management & Performance Analytics')
st.caption('CSC8101 OOP Course Project | Demonstration data are synthetic, not official Judiciary statistics.')
st.sidebar.header('Data & filters')
source=st.sidebar.file_uploader('Upload court data (CSV)',type='csv')
try:
    repo = CourtRepository.from_frame(pd.read_csv(source)) if source else CourtRepository.from_csv(Path(__file__).parent/'data'/'synthetic_courts.csv')
    details=PerformanceAnalyzer(repo).detailed()
    if details.empty:
        st.warning('The dataset contains no records.'); st.stop()
    years=st.sidebar.multiselect('Financial-year ending year',sorted(details.year.unique()),default=sorted(details.year.unique()))
    regions=st.sidebar.multiselect('Regions',sorted(details.region.unique()),default=sorted(details.region.unique()))
    selected=details[details.year.isin(years)&details.region.isin(regions)].copy()
    if selected.empty:
        st.warning('No records match the selected filters.'); st.stop()
    filtered=PerformanceAnalyzer(CourtRepository.from_frame(selected)).aggregate()
    totals=filtered.iloc[0]
    cols=st.columns(5)
    metrics=[('Opening',totals.opening),('Registered',totals.registered),('Disposed',totals.disposed),('Closing',totals.closing),('Backlog',totals.backlog_closing)]
    for col,(label,value) in zip(cols,metrics):
        col.metric(label,f'{int(value):,}')
    st.subheader('Performance indicators')
    a,b,c=st.columns(3)
    a.metric('Clearance rate',f'{totals.clearance_rate:.1f}%' if pd.notna(totals.clearance_rate) else 'N/A')
    b.metric('Disposal rate',f'{totals.disposal_rate:.1f}%' if pd.notna(totals.disposal_rate) else 'N/A')
    c.metric('Backlog share',f'{totals.backlog_share:.1f}%' if pd.notna(totals.backlog_share) else 'N/A')
    st.caption('Clearance = disposed / registered; disposal = disposed / (opening + registered); backlog share = closing backlog / closing cases. Rates use aggregated counts, not averages of court percentages.')
    tabs=st.tabs(['Overview','Court comparisons','Forecasting','Data & export','About'])
    with tabs[0]:
        annual=PerformanceAnalyzer(CourtRepository.from_frame(selected)).aggregate(['year'])
        fig=px.line(annual,x='year',y=['registered','disposed','closing'],markers=True,title='Annual caseload trends',labels={'value':'Cases','year':'Year','variable':'Measure'})
        st.plotly_chart(fig,use_container_width=True)
        st.dataframe(annual,use_container_width=True,hide_index=True)
    with tabs[1]:
        courts=PerformanceAnalyzer(CourtRepository.from_frame(selected)).aggregate(['court'])
        st.plotly_chart(px.bar(courts.sort_values('closing',ascending=False),x='court',y=['closing','backlog_closing'],barmode='group',title='Pending cases and backlog by court'),use_container_width=True)
        st.dataframe(courts,use_container_width=True,hide_index=True)
    with tabs[2]:
        st.write('Illustrative extrapolation, not a validated operational forecast.')
        metric=st.selectbox('Forecast measure',['closing','registered','disposed','backlog_closing'])
        method=st.radio('Forecast method',['Linear trend','Last observed value'],horizontal=True)
        horizon=st.slider('Years ahead',1,5,3)
        model=LinearForecaster() if method=='Linear trend' else LastValueForecaster()
        try:
            prediction=ForecastService(model).forecast(selected,metric,horizon)
            history=selected.groupby('year',as_index=False)[metric].sum()
            history['series']='Observed'; history=history.rename(columns={metric:'cases'})
            future=prediction.rename(columns={'forecast':'cases'});future['series']='Forecast'
            combined=pd.concat([history[['year','cases','series']],future[['year','cases','series']]],ignore_index=True)
            st.plotly_chart(px.line(combined,x='year',y='cases',color='series',markers=True,title=f'{metric.replace("_"," ").title()} forecast'),use_container_width=True)
            st.dataframe(prediction,hide_index=True)
        except DataValidationError as exc:
            st.info(str(exc))
    with tabs[3]:
        st.dataframe(selected,use_container_width=True,hide_index=True)
        st.download_button('Download filtered records (CSV)',selected.to_csv(index=False).encode('utf-8'),'court_performance_filtered.csv','text/csv')
        st.write('Expected upload columns:',', '.join(['court','region','year','opening','registered','disposed','backlog_opening','backlog_closing']))
    with tabs[4]:
        st.markdown('**OOP:** CourtRecord encapsulates validated data; CourtRepository manages records; PerformanceAnalyzer calculates metrics; Forecaster is an abstract class; LinearForecaster and LastValueForecaster demonstrate inheritance and polymorphism; ForecastService uses composition.')
        st.warning('Synthetic dataset. Not a replacement for ECCMIS, CCAS or official Judiciary reporting. Backlog is supplied as an input; case-age information is not inferred.')
except (DataValidationError,ValueError,pd.errors.ParserError,KeyError) as exc:
    st.error(f'Could not process the dataset: {exc}')
