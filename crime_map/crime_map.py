import numpy as np
import string
import matplotlib.pyplot as plt
import pandas as pd
import geopandas
import seaborn as sns
from itertools import compress
from datetime import date
from bokeh.plotting import figure, output_file, show, ColumnDataSource, curdoc
from bokeh.tile_providers import get_provider, Vendors
from bokeh.layouts import row, column, widgetbox
from bokeh.models import ColumnDataSource, CategoricalColorMapper, HoverTool, DateRangeSlider
from bokeh.models.widgets import Select, Slider

sns.set_color_codes()

data = pd.read_csv('../clean_data/crime_data_clean.csv')

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

# For now, color by district (ten of them in New Haven)
clrs = sns.color_palette('husl', n_colors=10).as_hex()
label_color = [clrs[l-1] for l in gdata.DISTRICT.values]

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

#my_hover = HoverTool()
#my_hover.tooltips = [('Address of the point', '@address')]
# range bounds supplied in web mercator coordinates
p = figure(x_range=(-8126000, -8110000), y_range=(5051000, 5062000),
           x_axis_type="mercator", y_axis_type="mercator", tooltips=TOOLTIPS)
p.add_tile(tile_provider)

p.circle(x='x', y='y', source=source, size=8, alpha=0.7,line_color='black',fill_color='color') 

#TOOLTIPS = """
#    <div style="width:300px;">
#    @tweet
#    </div>
#    """

#show(p)

def update_plot(attr, old, new):
    #Update glyph locations
    time = range_slider.value_as_datetime
    mask = (gdata.index >= time[0]) & (gdata.index <= time[1])
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

range_slider = DateRangeSlider(start=start_date, end=end_date, value=(start_date, end_date), step=24*60*60*1000, title="Date Range", callback_policy = 'mouseup', tooltips = False, width=600)

range_slider.on_change('value',update_plot)

layout = column(p,widgetbox(range_slider))
curdoc().add_root(layout)
show(layout)
