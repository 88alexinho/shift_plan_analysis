import streamlit as st
import pandas as pd
import altair as alt
import numpy as np
    
st.set_page_config(
    page_title="UTG_MaintenanceApp",
    page_icon=None,
    layout="wide"
)

st.title('Shift plan aircraft maintenance UTG')

with st.container(border=True):
    st.subheader('Instructions for preparing a file for uploading to the UTG_MaintenanceApp application:')
    st.text('- generate an .xlsl file in GoogleDoc or Excel\n- transfer information from the letter to the generated file\n- check for information in the following columns:\n airline name, aircraft type, aircraft reg. number, package number, WO number, job description, work package, start time, end time, performer category, work intensity \n- check the column sequence STRICTLY as specified in the line above\n- fill in the performer category column (manually - based on experience in aviation)\n- delete the line with the column names\n- save the file in .CSV format\n- upload the file to the UTG_MaintenanceApp program')

    uploaded_file = st.file_uploader("Upload a CSV file", type='csv')
    if uploaded_file is not None:

        df = pd.read_csv(uploaded_file)
        # df = pd.read_csv(r'C:\Users\Alex\data_analysis\streamlit_project\streamlit_app\shift_planSP.csv')
        

        columns = ['airlines', 'ac_type','reg_number', 'package','wo#','description','start_time','end_time','station','cat','man_hours']

        # определяем название колонок для признаков:
        df.columns = columns

        # удаляем столбец station (по причине отсутствия необходимости в использовании):
        df.drop('station',axis=1, inplace=True)

        # переводим столбцы start_time, end_time в формат datetime.
        df['start_time'] = pd.to_datetime(df['start_time'])
        df['end_time'] = pd.to_datetime(df['end_time'])

        # меняем запятую в строке man_hours на точку для перевода в формат float и проведения арифметических операций.
        df['man_hours'] = df['man_hours'].str.replace(',','.')

        # переводим столбец man_hours в формат float.
        df['man_hours'] = df['man_hours'].astype(float)
        # создадим столбец time_slot - как разница между временем конца ТО и временем начала ТО.
        df['time_slot'] = round(((df['end_time'] - df['start_time']).dt.components['hours']*60 + (df['end_time'] - df['start_time']).dt.components['minutes'])/60,2)
        # группируем данные по пакетам ТО на ВС.   
        ac_pack_dist = df.groupby(['ac_type','reg_number','package','start_time','end_time','cat']).agg({'man_hours':'sum','time_slot':'max'}).sort_values('ac_type')
        # определяем столбец man_count, как количество специалистов, необходимых для выполнения пакета работ на ВС.
        ac_pack_dist['mans_count'] = round(ac_pack_dist['man_hours'] / ac_pack_dist['time_slot'],2)

        ac_pack_dist_gr = df.groupby(['ac_type','reg_number','package','start_time','end_time','cat'],as_index=False).agg({'man_hours':'sum','time_slot':'max'}).sort_values('ac_type')
        # округлим столбец man_hours до одного знака после запятой.
        ac_pack_dist_gr['man_hours'] = round(ac_pack_dist_gr['man_hours'],1)
        # переведем столбец man_hours в формат строки, для создания chart_1.
        ac_pack_dist_gr['man_hours'] = ac_pack_dist_gr['man_hours'].astype(str)

        hard_work = df.query('man_hours > 4 or cat=="STR" or cat=="NDT"').iloc[:,:-1].reset_index(drop=True).sort_values(by='man_hours',ascending=False)

        all_works = df.iloc[:,:-1]

        # ////////////////////////////////////////chart vizualization//////////////////////////////////////////////////// 
        # chart_1
        # создадим df для визуализации chart_1
        ac_pack_dist_gr_ch_1 = ac_pack_dist_gr.groupby(['ac_type','reg_number','package','start_time','end_time'],as_index=False)[['cat','man_hours']].agg(' / '.join)
        chart_1 = alt.Chart(ac_pack_dist_gr_ch_1).mark_bar().encode(
            x='start_time',
            x2='end_time',
            y='reg_number',
            color=alt.Color('ac_type', scale=alt.Scale(scheme='tableau20')),
            tooltip=['package','cat','man_hours']
        ).properties(height=500,title='Shift plan')
        text_ch_1 = chart_1.mark_text(
            align="left",
            baseline="middle",
            dx=5,
            dy=0,
            fontSize=12,
            fontWeight='bold',
            fill= "black"
        ).encode(text="cat")
        full_ch_1 = chart_1 + text_ch_1

        # chart_2
        ac_pack_dist_gr_ch_2 = df.groupby(['reg_number','cat'],as_index=False).agg({'man_hours':'sum'})
        ac_pack_dist_gr_ch_2['man_hours'] = np.ceil(ac_pack_dist_gr_ch_2['man_hours'])
        chart_2 = alt.Chart(ac_pack_dist_gr_ch_2).mark_bar().encode(
            x=alt.X('reg_number', axis=alt.Axis(labelAngle=0,grid=True)),
            xOffset='cat',
            y=alt.Y('man_hours', axis=alt.Axis(grid=True)),
            color=alt.Color(field="cat", type="nominal",scale=alt.Scale(scheme='viridis'))
        ).properties(height=500,title='Man hours distribution by reg number and cat. performer')
            
        text_ch_2 = chart_2.mark_text(
            align="center",
            baseline="line-top",
            dx=5,
            dy=-15,
            fontSize=12,
            fontWeight='bold',
            fill='white'
        ).encode(text="man_hours")

        full_ch_2 = chart_2 + text_ch_2

        # chart_3
        ac_pack_dist_gr_ch_3 = df.groupby(['cat'],as_index=False).agg({'man_hours':'sum'})
        chart_3 = alt.Chart(ac_pack_dist_gr_ch_3).mark_arc(radius=90,padAngle = 0.05).encode(
        theta=alt.Theta(field="man_hours", type="quantitative", stack=True),
        color=alt.Color(field="cat", legend=alt.Legend(title=None,orient="none",direction='horizontal',titleAnchor='middle'),scale=alt.Scale(scheme='viridis'))).properties(
            height=250, width=200,
            title="Category"
        )
        text_ch_3 = chart_3.mark_text(radius=75,fill= "black", fontSize=14, fontWeight='bold').encode(alt.Text(field="man_hours", type="quantitative", format=",.1f"))

        full_ch_3 = alt.layer(chart_3, text_ch_3, data=ac_pack_dist_gr_ch_3).resolve_scale(theta="independent")

        # chart_4
        ac_pack_dist_gr_ch_4 = df.groupby(['ac_type',],as_index=False).agg({'man_hours':'sum'})
        chart_4 = alt.Chart(ac_pack_dist_gr_ch_4).mark_arc(radius=90,padAngle = 0.05).encode(
        theta=alt.Theta(field="man_hours", type="quantitative",stack=True),
        color=alt.Color(field="ac_type",legend=alt.Legend(title=None,orient='none',direction='horizontal',titleAnchor='middle'),scale=alt.Scale(scheme='tableau20'))
        ).properties(
            height=250, width=200,
            title="AC type"
        )
        text_ch_4 = chart_4.mark_text(radius=75, fill='black',fontSize=14, fontWeight='bold').encode(alt.Text(field="man_hours", type="quantitative", format=",.1f"))

        full_ch_4 = alt.layer(chart_4, text_ch_4, data=ac_pack_dist_gr_ch_4).resolve_scale(theta="independent")

        #chart_7

        ac_pack_dist_gr_ch_7 = df.groupby(['airlines','ac_type','cat'],as_index=False).agg({'man_hours':'sum'})
        ac_pack_dist_gr_ch_7['man_hours'] = np.ceil(ac_pack_dist_gr_ch_7['man_hours'])

        chart_7 = alt.Chart(ac_pack_dist_gr_ch_7).mark_bar().encode(
        x=alt.X('ac_type', axis=alt.Axis(labelAngle=0,grid=True)),
        xOffset='cat',
        y=alt.Y('man_hours', axis=alt.Axis(grid=True)),  
        color=alt.Color(field="cat", type="nominal",scale=alt.Scale(scheme='viridis')),
        ).properties(height=420, width=610,title='Man hours distribution by airlines',)

        text_ch_7 = chart_7.mark_text(
            align="center",
            baseline="line-top",
            dx=5,
            dy=-15,
            fontSize=14,
            fontWeight = 'bold',
            fill= "white"
        ).encode(text="man_hours")
        full_ch_7 = (chart_7 + text_ch_7)

        # full_chart
        full_chart = ((full_ch_3 | full_ch_4).resolve_scale(color='independent') & full_ch_1 & full_ch_2).resolve_scale(color='independent')

        col1, col2 = st.columns([1, 1.55],vertical_alignment='top')

        with col1:
            st.altair_chart(full_ch_7, theme="streamlit", use_container_width=True)

        with col2:
            st.dataframe(ac_pack_dist)

        # st.write((full_ch_1 & full_ch_2).resolve_scale(color='independent'))
        st.altair_chart(full_ch_1, theme="streamlit", use_container_width=True)
        st.altair_chart(full_ch_2, theme="streamlit", use_container_width=True)
        st.dataframe(hard_work,use_container_width=True)
        st.dataframe(all_works,use_container_width=True)
        
#         col3, col4 = st.columns(2,vertical_alignment='top')
#         with col3:
#             staff_737CL_B1 = st.number_input("B737CL B1", 0, 25, 0, 1)    
#             staff_737NG_B1 = st.number_input("B737NG B1", 0, 25, 0, 1)
#             staff_767_B1 = st.number_input("B767 B1", 0, 25, 0, 1)
#             staff_SSJ_B1 = st.number_input("SSJ B1", 0, 25, 0, 1)
#             staff_CAB = st.number_input("CAB", 0, 25, 0, 1)
#             staff_NDT = st.number_input("NDT", 0, 25, 0, 1)
#             staff_STR = st.number_input("STR", 0, 25, 0, 1)
            
#         with col4:
#             staff_737CL_B2 = st.number_input("B737CL B2", 0, 25, 0, 1)*10
#             staff_737NG_B2 = st.number_input("B737NG B2", 0, 25, 0, 1)
#             staff_767_B2 = st.number_input("B767 B2", 0, 25, 0, 1)
#             staff_SSJ_B2 = st.number_input("SSJ B2", 0, 25, 0, 1)

# # 'B737CL B1':staff_737CL_B1,'B737NG B1':,'B767 B1','SSJ B1','B737CL B2','B737NG B2','B767 B2','SSJ B2','CAB','NDT','STR'),(,staff_737NG_B1,staff_767_B1,staff_SSJ_B1,staff_737CL_B2,staff_737NG_B2,staff_767_B2,staff_SSJ_B2,staff_CAB,staff_NDT,staff_STR))

#         ac_type_cat = ['B737CL B1','B737NG B1','B767 B1','SSJ B1','B737CL B2','B737NG B2','B767 B2','SSJ B2','CAB','NDT','STR']
#         len(ac_type_cat)
#         mh_count = [staff_737CL_B1,staff_737NG_B1,staff_767_B1,staff_SSJ_B1,staff_737CL_B2,staff_737NG_B2,staff_767_B2,staff_SSJ_B2,staff_CAB,staff_NDT,staff_STR]

#         df_staff = pd.DataFrame({'ac_type_cat':ac_type_cat, 'mh_count':mh_count})
#         # column = ['count']
#         # df_staff.columns = column

#         df_staff_plan = df.query('cat not in ["CAB","NDT","STR"]').groupby(['ac_type','cat'],as_index=False)['man_hours'].sum()
#         ac_type_cat = df_staff_plan['ac_type'] + ' ' + df_staff_plan['cat']

#         df_staff_plan.insert(0,'ac_type_cat',ac_type_cat)
#         df_staff_plan = df_staff_plan.drop(['ac_type','cat'],axis=1)

#         df_cab_str_ndt = df.query('cat=="CAB" or cat=="NDT" or cat=="STR"').groupby('cat',as_index=False)['man_hours'].sum()
#         df_cab_str_ndt = df_cab_str_ndt.rename(columns={'cat':'ac_type_cat'})

#         vertical_concat = pd.concat([df_staff_plan, df_cab_str_ndt], axis=0, ignore_index=True) # concatenating along rows


        # df_staff_plan['man_hours'] = np.ceil(df_staff_plan['man_hours'])
        # st.write(vertical_concat)
        # st.write(df_staff,height=800)