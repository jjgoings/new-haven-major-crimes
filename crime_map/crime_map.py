import numpy as np
import string
import pandas as pd
import geopandas
import seaborn as sns
from itertools import compress
from datetime import date
from bokeh.plotting import figure, output_file, show, ColumnDataSource, curdoc
from bokeh.tile_providers import get_provider, Vendors
from bokeh.layouts import row, column, widgetbox, layout
from bokeh.models import ColumnDataSource, CategoricalColorMapper, HoverTool, DateRangeSlider, CheckboxGroup, CustomJS, Select, MultiChoice, MultiSelect, CheckboxButtonGroup, Paragraph, Div 
from bokeh.models.widgets import Select, Slider
from bokeh.models.annotations import Legend


data = pd.read_csv('./clean_data/crime_data_clean.csv')

# Clean up some types and formats
data['CASE_NUMBER'] = data['CASE_NUMBER'].astype('Int64')
data['DISTRICT'] = data['DISTRICT'].astype('Int64')
data['ADDRESS'] = data['ADDRESS'].apply(lambda x: string.capwords(x))
data['CHRG_DESC'] = data['CHRG_DESC'].str.title()
data = data.set_index(pd.to_datetime(data['DATETIME']))
data.index = data.index.tz_localize(None) # We will assume everything is local time

# Split the latitude and longitude for geo-plotting, and drop combined column 
data[['lat','lon']] = data.LAT_LONG.str.split(',',expand=True).astype(np.float)
data = data.drop(columns=['LAT_LONG'])

# We will use GeoPandas from hereon
gdata = geopandas.GeoDataFrame(
    data, geometry=geopandas.points_from_xy(data.lon, data.lat))

# Lat/Long to World Geodetic System 1984 (need GPS coords to plot)
gdata.crs = "EPSG:4326"
gdata = gdata.to_crs(epsg=3857)

# For now, color by type of major crime  
crime_types = gdata.CHRG_DESC.unique()
clrs = sns.color_palette('Paired', n_colors=len(crime_types)).as_hex()
# map each unique crime to an integer so we can match it with a color
clr_dict = {crime_types[i] : i for i in range(0,len(crime_types))}
label_color = [clrs[clr_dict[l]] for l in gdata.CHRG_DESC.values]

#crime_select = Select(title="Crime", value="All",
#               options=['All']+list(crime_types))
crime_select = MultiChoice(title="Crime Type:", value=list(crime_types),
               options=list(crime_types),height=400)

source = ColumnDataSource(data=dict(
    x=gdata.geometry.x,
    y=gdata.geometry.y,
    date = gdata.index.format(formatter=lambda x: x.strftime('%m-%d-%Y  %I:%M %p')),
    address = gdata.ADDRESS,
    desc = gdata.CHRG_DESC,
    color=label_color,
))

# Creating the figure
tile_provider = get_provider(Vendors.CARTODBPOSITRON)

TOOLTIPS = [
    ("Date", "@date"),
    ("Address", "@address"),
    ("Description", "@desc"),
]

# range bounds supplied in web mercator coordinates
p = figure(x_range=(-8126000, -8110000), y_range=(5049000, 5065000),
           x_axis_type="mercator", y_axis_type="mercator", tooltips=TOOLTIPS, title='Major Crime in New Haven, CT from %s to %s' % (gdata.index.min().strftime('%d %b %Y'),gdata.index.max().strftime('%d %b %Y')),
           plot_height=600,plot_width=800)
p.add_tile(tile_provider)

p.circle(x='x', y='y', source=source, size=8, alpha=0.8,line_color='black',fill_color='color') 

# add custom legend
items = []
for i,name in enumerate(crime_types):
    items += [(name,[p.circle(i,i,color=clrs[i],size=8,alpha=0.8,line_color='black')])]
legend = Legend(items=items)
p.add_layout(legend,'center')
p.legend.location='bottom_left'


def update_plot(attr, old, new):
    #Update glyph locations
    time = range_slider.value_as_datetime
    crime = crime_select.value 
    p.title.text = 'Major Crime in New Haven, CT from %s to %s' % (time[0].strftime('%d %b %Y'),time[1].strftime('%d %b %Y')) 
    p.title.align = "left"
    mask = (gdata.index >= time[0]) & (gdata.index <= time[1]) & (gdata.CHRG_DESC.isin(crime))
    new_data = {
        'x': gdata.loc[mask].geometry.x, 
        'y': gdata.loc[mask].geometry.y, 
        'date': gdata.loc[mask].index.format(formatter=lambda x: x.strftime('%m-%d-%Y  %I:%M %p')),
        'address': gdata.loc[mask].ADDRESS,
        'desc': gdata.loc[mask].CHRG_DESC,
        'color': list(compress(label_color,mask))
       
    }
    source.data = new_data

start_date = gdata.index.min()
end_date = gdata.index.max()

range_slider = DateRangeSlider(start=start_date, end=end_date, value=(start_date, end_date), step=24*60*60*1000, title="Date Range", tooltips = False, width=800)


legend_button = CheckboxButtonGroup(
        labels=["Show Legend"], active=[0])

def change_click(attr,old,new):
    p.legend.visible = not(p.legend.visible)

range_slider.on_change('value',update_plot)
crime_select.on_change('value',update_plot)
legend_button.on_change('active',change_click)

text = Paragraph(text="""
""",
width=200, height=100)

attribution = Div(text="""
&copy; 2020 Joshua Goings. Data from the <a href="https://www.newhavenct.gov/gov/depts/nhpd/compstat_reports.htm">New Haven Police Department</a>. Last updated 18 Apr 2020.
""",
width=800, height=20,style={'font-size': '80%', 'color': 'gray'})

widgets = column(text,crime_select,legend_button,width=300)
layout = layout([[p,widgets],[range_slider],[attribution]])

curdoc().add_root(layout)
curdoc().title="Crime in New Haven, CT"
#show(layout)
