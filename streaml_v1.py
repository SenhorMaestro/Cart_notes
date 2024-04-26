import streamlit as st
import numpy as np
import pandas as pd
import time
import matplotlib.pyplot as plt
from streamlit_echarts import st_echarts
import os
url = os.getenv('url')

df = pd.read_csv('chizh.csv')
df = df[['name','img_source','category','price']]
df['img_source'] = df['img_source'].apply(lambda x: url+x)
df['quantity'] = 1.00

st.header('Ваш список покупок')
st.write('Выберите товары из ассортимента магазина')

def flatten_comprehension(matrix):
    if len(matrix) != 0:
        return [item for row in matrix for item in row]
    else: 
        return matrix

search = st.text_input('Введите название или марку', '', placeholder='например, бананы или 7 days...')
df_with_selections = df.copy()
col0, col1= st.columns(2)
selected_category = col0.selectbox('Выберите категорию',['Select all']+df['category'].unique().tolist(),index=0)
col1.write('')
col1.write('')
add = col1.button('Добавить в корзину', help='Выбранные товары добавятся в корзину')

def dataframe_with_selections(df):
    df_with_selections = df.copy()

    if selected_category!='Select all' :
        df_with_selections = df_with_selections[df_with_selections['category']==selected_category]
    df_with_selections = df_with_selections.query('name.str.contains("%s", case=False)' %search, engine='python')
    df_with_selections.insert(0, "Select", False)

    # Get dataframe row-selections from user with st.data_editor
    edited_df = st.data_editor(
        df_with_selections,
        hide_index=True,
        column_config={"Select": st.column_config.CheckboxColumn(required=True), 
                       "img_source": st.column_config.ImageColumn("Preview Image", 
                                                                  help="Дважды коснитесь картинки для увеличения"),
        
        },
        disabled=['name','img_source','ref','category','price','date','quantity']
    )

    # Filter the dataframe using the temporary column, then drop the column
    selected_rows = edited_df[edited_df.Select]
    selected_indexes = selected_rows.index.tolist()
    total = (selected_rows['price']*selected_rows['quantity']).sum()
    return selected_rows.drop('Select', axis=1), total, selected_indexes

def cart_config(df2):
    df_cart = st.data_editor(
            df2,
            hide_index=False,
            column_config={"Куплено": st.column_config.CheckboxColumn(required=True), 
                        "img_source": st.column_config.ImageColumn("Preview Image", 
                                                                    help="Дважды коснитесь картинки для увеличения"),
                            "quantity": st.column_config.NumberColumn(
                "Quantity or weight",
                help="Количество товаров или вес (для овощей и фруктов)",
                min_value=0,
                max_value=20,
                format="%.2f",
            )
            },
            num_rows="dynamic",
            disabled=['name','img_source','ref','category','price','date']
        )
    selected_rows = df_cart[df_cart["Куплено"]==True]
    selected_bought_indexes = selected_rows.index.tolist()
    
    summary = df_cart.groupby('category').apply(lambda x: (x['price'] * x['quantity']).sum())
    df_cat = summary.to_frame(name='spent')
    list_of_quantity_by_index = []
    for i in zip(df_cart.index.tolist(), df_cart['quantity']):
        list_of_quantity_by_index.append(i)
    return df_cart, selected_bought_indexes, list_of_quantity_by_index, df_cat


if add:
    selection, total_bill, selected_indexes = dataframe_with_selections(df)
    for i in selected_indexes:
        st.session_state.mdf1.append(i)
else:
    selection, total_bill, selected_indexes = dataframe_with_selections(df)


if "mdf" not in st.session_state: 
    st.session_state.mdf = pd.DataFrame(columns=['Location'])
if "mdf1" not in st.session_state:
    st.session_state.mdf1 =  []
if "mdf2" not in st.session_state:
    st.session_state.mdf2 =  [] #индексы купленных товаров
if "mdf3" not in st.session_state:
    st.session_state.mdf3 =  []


st.write('')
st.write('')
st.write('')
run = st.button('Обновить корзину')


print(st.session_state.mdf1)




with st.form("my_form", clear_on_submit=True):
    st.subheader("Ваша корзина:")
    st.write('В корзине вы можете указать нужное число товаров или вес для фруктов и овощей, а также отметить галочкой уже купленные товары')
    col_form0, col_form1 = st.columns(2)
    with col_form0:
        delete = st.form_submit_button("Внести изменения",help='Пересчитать чек / удалить товар из корзины')
    with col_form1:
        st.write('**ВАЖНО: Чтобы сохранить сделанные изменения нажмите "Внести изменения", а затем нажмите "Обновить корзину", чтобы внесённые изменения отобразились корректно**')
    total = 0
    if len(st.session_state.mdf1) != 0:
        df2 = df.iloc[st.session_state.mdf1]
        df2.insert(0, "Куплено", False)
        for i in st.session_state.mdf2:
            df2.at[i, 'Куплено'] = True
        for tpl in st.session_state.mdf3:
            df2.at[tpl[0], 'quantity'] =  tpl[1]
        df_cart, already_bought, list_of_quantity_by_index, df_cat = cart_config(df2)
        print('------------------------------')
        print(df_cat)
    
        total=(df_cart['price']*df_cart['quantity']).sum()
        total_items=df_cart['name'].nunique()
        removed_index = st.number_input('Чтобы удалить товар из корзины, введите его индекс, затем нажмите "Внести изменения" или Enter. Чтобы увидеть применённые изменения нажмите "Обновить корзину"', min_value=0, max_value=2000, value=None,placeholder="Введите индекс товара...", step=1)
        
    
        print('alr_bought=%s' %already_bought)
    
        st.session_state.mdf2 = already_bought
        st.session_state.mdf3 = list_of_quantity_by_index
        print('st.session_state.mdf2=')
        print(st.session_state.mdf2)
        print('st.session_state.mdf3=')
        print(st.session_state.mdf3)
        
        if delete:
            if removed_index in st.session_state.mdf1:
                st.session_state.mdf1.remove(removed_index)
            print('after pressing button st.session_state.mdf1=%s' %st.session_state.mdf1)
            if len(st.session_state.mdf2) != 0 and removed_index in st.session_state.mdf2:
                st.session_state.mdf2.remove(removed_index)
                print('after pressing button st.session_state.mdf2=%s' %st.session_state.mdf2)
            if len(st.session_state.mdf3) != 0:
                for tpl in st.session_state.mdf3:
                    if tpl[0] == removed_index:
                        st.session_state.mdf3.remove(tpl)
                print('after pressing button st.session_state.mdf3=%s' %st.session_state.mdf3)
            

    else:
        st.write('Начните наполнять вашу корзину')

    
st.metric(label="ИТОГО:", value="%.2f руб." %total)



try:
    st.subheader("Расходы по категориям",divider='violet')
    
    fig, ax = plt.subplots(figsize=(6, 3), subplot_kw=dict(aspect="equal"))

    text=list(df_cat.index)


    data = list(df_cat['spent'])

    wedges, texts = ax.pie(data, wedgeprops=dict(width=0.5),startangle=-40)

    bbox_props = dict(boxstyle="square,pad=0.3", fc="w", ec="k", lw=0.72)
    kw = dict(arrowprops=dict(arrowstyle="-"),
          bbox=bbox_props, zorder=0, va="center")

    for i, p in enumerate(wedges):
        ang = (p.theta2 - p.theta1)/2. + p.theta1
        y = np.sin(np.deg2rad(ang))
        x = np.cos(np.deg2rad(ang))
        horizontalalignment = {-1: "right", 1: "left"}[int(np.sign(x))]
        connectionstyle = f"angle,angleA=0,angleB={ang}"
        kw["arrowprops"].update({"connectionstyle": connectionstyle})
        ax.annotate(text[i], xy=(x, y), xytext=(1.35*np.sign(x), 1.4*y),
                    horizontalalignment=horizontalalignment, **kw)



    st.pyplot(fig)


    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Всего различных товаров", divider='green')
        colors = ["#f36d54","#fabd57","#f6ee54","#c1da64"]
        values = [24, 18, 12, 6, 0]

        fig1 = plt.figure(figsize=(10,10))

        ax = fig1.add_subplot(projection="polar")

        ax.bar(x=[0, 0.79, 1.57, 2.36], width=0.79, height=0.5, bottom=2,
            linewidth=5, edgecolor="white",
            color=colors, align="edge")

        for loc, val in zip([0, 0.79, 1.57, 2.36 , 3.14], values):
            plt.annotate(val, xy=(loc, 2.5),
                    ha="right" if val<=15 else "left")

        total_items_1 = int(total_items) if total_items <=24 else 24
        dict_scale = {0: 3.14,
                    1: 3.01,
                    2: 2.88,
                    3: 2.75,
                    4: 2.62,
                    5: 2.49,
                    6: 2.36,
                    7: 2.22,
                    8: 2.10,
                    9: 1.96,
                    10: 1.83,
                    11: 1.70,
                    12: 1.57,
                    13: 1.44,
                    14: 1.31,
                    15: 1.18,
                    16: 1.05,
                    17: 0.92,
                    18: 0.79,
                    19: 0.65,
                    20: 0.52,
                    21: 0.39,
                    22: 0.26,
                    23: 0.13,
                    24: 0}
        plt.annotate(str(total_items_1), xytext=(0,0), xy=(dict_scale[total_items_1], 2.0),
                    arrowprops=dict(arrowstyle="wedge, tail_width=0.5", color="black", shrinkA=0),
                    bbox=dict(boxstyle="circle", facecolor="black", linewidth=2.0, ),
                    fontsize=45, color="white", ha="center"
                    )



        ax.set_axis_off()

        st.pyplot(fig1)


    with col_b:
        st.subheader("Заполненность корзины*", divider='blue')
        liquidfill_option1 = {
            "series": [{"type": "liquidFill", "data": [total_items/14, 0.060*total_items, 0.047*total_items, 0.036*total_items]}]
            }
        st_echarts(liquidfill_option1)
        st.write("*Из расчёта норма приблилизительно = 14 товаров")

    data_word = [
    {"name": name, "value": value}
    for name, value in [
        ("чижик", "999"),
        ("покупки", "888"),
        ("выгода", "777"),
        ("круассанчики", "688"),
        ("фрукты", "588"),
        ("овощи", "516"),
        ("скидки", "515"),
        ("акции", "483"),
        ("молоко", "462"),
        ("торты", "449"),
        ("мороженое", "429"),
        ("крупы", "407"),
        ("вафли", "406"),
        ("пельмени", "406"),
        ("бананы", "386"),
        ("огурцы", "385"),
        ("сосиски", "375"),
        ("сливки", "355"),
        ("выпечка", "355"),
        ("чай", "335"),
        ("рыба", "324"),
        ]
    ]
    wordcloud_option = {"series": [{"type": "wordCloud", "data": data_word}]}
    st_echarts(wordcloud_option)
except:
    print('except')

