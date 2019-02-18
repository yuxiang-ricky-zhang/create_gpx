
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import os 
import xml.etree.cElementTree as ET
import time

class ImageMetaData(object):

    exif_data = None
    image = None

    def __init__(self, img_path):
        self.image = Image.open(img_path)
        self.get_exif_data()
        super(ImageMetaData, self).__init__()

    def get_exif_data(self):
        """
        Returns exif data 
        """
        exif_data = {}
        info = self.image._getexif()
        if info:
            for tag, value in info.items():
                decoded = TAGS.get(tag, tag)
                if decoded == "GPSInfo":
                    gps_data = {}
                    for t in value:
                        sub_decoded = GPSTAGS.get(t, t)
                        gps_data[sub_decoded] = value[t]

                    exif_data[decoded] = gps_data
                else:
                    exif_data[decoded] = value
        self.exif_data = exif_data
        return exif_data

    def get_if_exist(self, data, key):
        if key in data:
            return data[key]
        return None

    def convert_to_degress(self, value):

        """
        convert the GPS coordinates to degress
        """
        d0 = value[0][0]
        d1 = value[0][1]
        d = float(d0) / float(d1)

        m0 = value[1][0]
        m1 = value[1][1]
        m = float(m0) / float(m1)

        s0 = value[2][0]
        s1 = value[2][1]
        s = float(s0) / float(s1)

        return d + (m / 60.0) + (s / 3600.0)

    def get_lat_lng(self):
        """
        Returns the latitude, longitude, altitude and heading
        """
        alt = None
        lat = None
        lng = None
        heading = None
        exif_data = self.get_exif_data()

        if "GPSInfo" in exif_data:      
            gps_info = exif_data["GPSInfo"]
            gps_latitude = self.get_if_exist(gps_info, "GPSLatitude")
            gps_latitude_ref = self.get_if_exist(gps_info, 'GPSLatitudeRef')
            gps_longitude = self.get_if_exist(gps_info, 'GPSLongitude')
            gps_longitude_ref = self.get_if_exist(gps_info, 'GPSLongitudeRef')
            gps_altitude = self.get_if_exist(gps_info, 'GPSAltitude')
            gps_altitude_ref = self.get_if_exist(gps_info, 'GPSAltitudeRef')
            alt = gps_altitude[0]/gps_altitude[1]
            heading_raw = self.get_if_exist(gps_info, 'GPSImgDirection')
            heading = heading_raw[0]/heading_raw[1]
            if gps_latitude and gps_latitude_ref and gps_longitude and gps_longitude_ref:
                lat = self.convert_to_degress(gps_latitude)
                if gps_latitude_ref != "N":                     
                    lat = 0 - lat
                lng = self.convert_to_degress(gps_longitude)
                if gps_longitude_ref != "E":
                    lng = 0 - lng
        return lat, lng, alt, heading

    def get_timestamp(self):
        exif_data = self.exif_data
        if "DateTimeOriginal" in exif_data:
            timestamp = exif_data["DateTimeOriginal"]
            return timestamp




if __name__ == '__main__':

	in_dir = './'
	in_format = '.jpg'
	outfile_name = './myGPX.gpx'

	filelist = sorted(os.listdir(in_dir))

	xml_root = ET.Element("gpx")

	meta = ET.SubElement(xml_root, "metadata")

	trk = ET.SubElement(xml_root, "trk")
	name = ET.SubElement(trk,"name")
	name.text = 'DBSC'
	trk_type = ET.SubElement(trk,"type")
	trk_type.text = '10'

	trkseg = ET.SubElement(trk, "trkseg")

	count = 0
	# Loop through each file in the directory
	for filename in filelist:
		# For each image
	    if filename.endswith(in_format):
	    	meta_data =  ImageMetaData(filename)
	    	lat, lng, alt, heading = meta_data.get_lat_lng()
	    	if lat is not None and lng is not None and alt is not None and heading is not None:
		    	timestamp = meta_data.get_timestamp()
		    	time_struc  = time.strptime(timestamp, "%Y:%m:%d %H:%M:%S")	
		    	time_string = time.strftime("%Y-%m-%dT%H:%M:%SZ", time_struc)


		    	if count == 0:
		    		time_start = ET.SubElement(meta, "time")
		    		time_start.text = time_string

		    	# Each data point
		    	trkpt = ET.SubElement(trkseg, "trkpt", {'lat':str(round(lat,6)), 'lon':str(round(lng,6))})
		    	ele = ET.SubElement(trkpt, "ele")
		    	ele.text = str(alt)
		    	timetag = ET.SubElement(trkpt, "time")
		    	timetag.text = time_string

		    	count += 1


	#export
	tree = ET.ElementTree(xml_root)
	tree.write(outfile_name, encoding="utf-8", xml_declaration=True, method='xml')
