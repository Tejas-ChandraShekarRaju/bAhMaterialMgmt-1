from constants.constants import project_fields

#create a python class project with fields from project_fields

class projects(object):
    def __init__(self, project_number, project_name,package_type, project_location, no_of_floors, project_value, date_of_initial_advance, date_of_agreement, sales_executive, site_area, basement_slab_area, gf_slab_area, ff_slab_area, sf_slab_area, tf_slab_area, tef_slab_area, shr_oht, additional_cost, elevation_details, paid_percentage, comments, is_approved, cost_sheet, site_inspection_report):
        self.project_number = project_number
        self.project_name = project_name
        self.package_type = package_type
        self.project_location = project_location
        self.no_of_floors = no_of_floors
        self.project_value = project_value
        self.date_of_initial_advance = date_of_initial_advance
        self.date_of_agreement = date_of_agreement
        self.sales_executive = sales_executive
        self.site_area = site_area
        self.basement_slab_area = basement_slab_area
        self.gf_slab_area = gf_slab_area
        self.ff_slab_area = ff_slab_area
        self.sf_slab_area = sf_slab_area
        self.tf_slab_area = tf_slab_area
        self.tef_slab_area = tef_slab_area
        self.shr_oht = shr_oht
        self.additional_cost = additional_cost
        self.elevation_details = elevation_details
        self.paid_percentage = paid_percentage
        self.comments = comments
        self.is_approved = is_approved
        self.cost_sheet = cost_sheet
        self.site_inspection_report = site_inspection_report
        #define a defauult constructor

        self.package_types = {'Essential':'false','Premium':'false','Luxury':'false','Green Home':'false','Others':'false'}

        self.floors = {'G + 1':'false','G + 2':'false','G + 3':'false','G + 4':'false'}

        self.percentages = {'2.5':'false','5':'false','10':'false'}

        
        if package_type in self.package_types:
            self.package_types[package_type] = 'true'
        else:
            self.package_types[package_type] = 'false'

        if no_of_floors in self.floors:
            self.floors[no_of_floors] = 'true'
        else:
            self.floors[no_of_floors] = 'false'

        if paid_percentage in self.percentages:
            self.percentages[paid_percentage] = 'true'
        else:
            self.percentages[paid_percentage] = 'false'

