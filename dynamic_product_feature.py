# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import api
from openerp.fields import Integer, One2many, Html
from openerp.osv import fields, osv, orm
from openerp.tools.translate import _
from lxml import etree

class feature(osv.osv):
    _name = 'feature'
    _columns = {
        'name': fields.char('Feature Name'),
        'code': fields.char('Feature Code'),
        'product_field_id': fields.many2one('ir.model.fields', 'Product Field', readonly=True),
        'feature_category': fields.selection([('led_lighting','LED Lighting'),
                                ('led_signage','LED Signage'),
                                ('led_solar','LED Solar')],'Caterogy'),
        'product_feature_field_id':fields.many2one('ir.model.fields', 'Product Feature Field', readonly=True),
    }
    
    
    def create(self, cr, uid, vals, context=None):
        feature_name_list = vals.get('name').split( );
        feature_code_list = [ feature_name.lower()for feature_name in feature_name_list]
        vals['code'] = "_".join(feature_code_list)
        res = super(feature, self).create(
            cr, uid, vals, context=context)
        feature_data = self.browse(cr, uid, res, context=context)

        field_pool = self.pool['ir.model.fields']
        # For Product.Product
        column_values =  self.build_field_vals(cr, uid, feature_data, 'product.product', context=context)
        product_field_id = field_pool.create(cr, uid,column_values,)
        self.check_duplicate_field(cr, uid, product_field_id, 'product.product', context=context)
        
        # For Product.Fearute.Search
        column_values =  self.build_field_vals(cr, uid, feature_data, 'product.feature.search.wizard', context=context)
        product_feature_field_id = field_pool.create(cr, uid,column_values,)
        self.check_duplicate_field(cr, uid, product_feature_field_id, 'product.feature.search.wizard',context=context)
        
        self.write(cr, uid, [res], {'product_feature_field_id': product_feature_field_id,'product_field_id': product_field_id,}, context=context)
        return res
    
    def build_field_vals(self, cr, uid, feature_data, model_name , context=None):
        model_pool = self.pool['ir.model']
        model_ids = model_pool.search(
            cr, uid, [('model', '=', model_name)], context=context)
        field_name = 'x_' + feature_data.code.lower()
        return {
            'name': field_name,
            'model': 'model_name',
            'model_id': model_ids[0],
            'field_description': feature_data.name,
            'ttype': 'char',
            'size': 64,
            'state': 'manual',
            'modules':'dynamic_product_feature',
            
        }
    def check_duplicate_field(self, cr, uid, field_id, model_name, context=None):
        field_pool = self.pool['ir.model.fields']
        field = field_pool.browse(cr, uid, field_id, context=context)
        field_ids = field_pool.search(cr, uid, [
            ('name', '=', field.name),
            ('model', '=', model_name),
        ],
            context=context)
        if len(field_ids) > 1:
            raise orm.except_orm(
                _('Error'),
                _('Field %s (%s) already present')
                % field.name,model_name)
        return True
    


    def unlink(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        for feature_data in self.browse(cr, uid, ids, context=context):
            context['_force_unlink'] = True
            if feature_data.product_field_id:
                feature_data.product_field_id.unlink(context=context)
            if feature_data.product_feature_field_id:
                feature_data.product_feature_field_id.unlink(context=context)
        res = super(feature, self).unlink(
            cr, uid, ids, context=context)
        return res
    
    
"""
class features_value(osv.osv):
    _name = 'feature.value'
    _columns = {
        'feature_id': fields.many2one('feature', 'Feature'),
        'name': fields.char('Value')
    }
"""
class product_product(osv.osv):
    _inherit = 'product.product'
    
    _columns = {
        'feature_category': fields.selection([('led_lighting','LED Lighting'),
                                ('led_signage','LED Signage'),
                                ('led_solar','LED Solar')],'Caterogy')
    }
    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False,submenu=False):
        """
             Changes the view dynamically
             @param self: The object pointer.
             @param cr: A database cursor
             @param uid: ID of the user currently logged in
             @param context: A standard dictionary
             @return: New arch of view.
        """
        ret_val = super(product_product, self).fields_view_get(cr, uid, view_id, view_type, context, toolbar,submenu)
        fields = ret_val.get('fields',{})
        feature_obj = self.pool.get('feature')
        feature_ids = feature_obj.search(cr, uid, [], context=context)
        feature_records = feature_obj.browse(cr, uid, feature_ids, context=context)
        eview = etree.fromstring(
            ret_val['arch'])
        if view_type == 'form':
            feature_category_field = eview.xpath("//field[@name='feature_category']")[0]
            for feature_record in feature_records:
                field_name = feature_record.product_field_id.name
                ret_val['fields'].update(
                            {
                                field_name: {
                                    'string': feature_record.name,
                                    'type': 'char',
                                    'size': 64,
                                    'context': {}
                                }
                            }
                        )
                feature_category = False
                if feature_record.feature_category == 'led_lighting':
                    print"led_lighting>>>>>>>>>"
                    feature_category = '{"invisible": ["|",["feature_category","=","led_signage"],["feature_category","=","led_solar"]]}'
                elif feature_record.feature_category == 'led_signage':
                    print"led_signage>>>>>>>>>"
                    feature_category = '{"invisible": ["|",["feature_category","=","led_lighting"],["feature_category","=","led_solar"]]}'
                elif feature_record.feature_category == 'led_solar':
                    print"led_solar>>>>>>>>>"
                    feature_category = '{"invisible": ["|",["feature_category","=","led_lighting"],["feature_category","=","led_signage"]]}'
                #feature_category = '{"invisible": ["|",["feature_category","=","led_lighting"],["feature_category","=","led_signage"]]}'
                new_field = etree.Element(
                        'field', name=field_name, modifiers=feature_category)
                #feature_category_field.addnext(etree.Element('field', {'name': field_name, 'required': "1"}))
                feature_category_field.addnext(new_field)
               #feature_category_field.addnext(new_field)
            #ret_val['arch'] = etree.tostring(eview, encoding="utf-8")
            #print"Architecture>>>>>>>",ret_val['arch']
        elif view_type == 'search':
            print"In Serach Bar"
            feature_category_field = eview.xpath("//field[@name='feature_category']")[0]
            for feature_record in feature_records:
                field_name = feature_record.product_field_id.name
                ret_val['fields'].update(
                            {
                                field_name: {
                                    'string': feature_record.name,
                                    'type': 'char',
                                    'size': 64,
                                    'context': {}
                                }
                            }
                        )
                new_field = etree.Element(
                    'field', name=field_name, string=feature_record.name)
                feature_category_field.addnext(new_field)
               #feature_category_field.addnext(new_field)
        ret_val['arch'] = etree.tostring(eview, encoding="utf-8")
                
            
        return ret_val
    
    
    
class product_feature_search(osv.TransientModel):
    _name = 'product.feature.search.wizard'
    _description = 'Product Feature Search'
    
    
    def _product_feature_category_default(self, cr, uid, ids, context=None):

        product_feature_category_model, product_feature_category_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'custom_lightingome', 'product_category_led_lighting')
        #self.pool.get('stock.location').check_access_rule(cr, uid, [location_id], 'read', context=context)
        return product_feature_category_id

    _columns = {
            'product_feature_category':fields.selection([('led_lighting','LED Lighting'),('led_signage','LED Signage'),('led_solar','LED Solar')],'Product Feature Category'),
            
    }

    
    
    def product_category_change(self, cr, uid, ids, product_category, product_qty=0, context=None):
        """ Finds UoM of changed product.
        @param product_id: Id of changed product.
        @return: Dictionary of values.
        """
        result = {}
        if not product_category:
            return {'value': {
                'product_feature_category_id': False,
            }}
        product = self.pool.get('product.feature.category').search(cr, uid, [('code','=',product_category)], context=context)
        if product:
            result['value'] = {'product_feature_category_id': product[0],}
        return result    
    
    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False,submenu=False):
        """
             Changes the view dynamically
             @param self: The object pointer.
             @param cr: A database cursor
             @param uid: ID of the user currently logged in
             @param context: A standard dictionary
             @return: New arch of view.
        """
        ret_val = super(product_feature_search, self).fields_view_get(cr, uid, view_id, view_type, context, toolbar,submenu)
        if view_type == 'form':
            eview = etree.fromstring(
                        ret_val['arch'])
            fields = ret_val.get('fields',{})
            feature_obj = self.pool.get('feature')
            feature_ids = feature_obj.search(cr, uid, [], context=context)
            feature_records = feature_obj.browse(cr, uid, feature_ids, context=context)
            led_lighting_category_field = eview.xpath("//group[@name='led_lighting']")[0]
            led_signage_category_field = eview.xpath("//group[@name='led_signage']")[0]
            led_solor_category_field = eview.xpath("//group[@name='led_solor']")[0]
            for feature_record in feature_records:
                field_name = feature_record.product_feature_field_id.name
                ret_val['fields'].update(
                            {
                                field_name: {
                                    'string': feature_record.name,
                                    'type': 'char',
                                    'size': 64,
                                    'context': {}
                                }
                            }
                        )
                feature_category = False
                if feature_record.feature_category == 'led_lighting':
                    new_field = etree.Element(
                        'field', name=field_name)
                    led_lighting_category_field.insert(0,new_field)
                    
                elif feature_record.feature_category == 'led_signage':
                    new_field = etree.Element(
                        'field', name=field_name)
                    led_signage_category_field.insert(0,new_field)
                elif feature_record.feature_category == 'led_solar':
                    new_field = etree.Element(
                        'field', name=field_name)
                    led_solor_category_field.insert(0,new_field)
            ret_val['arch'] = etree.tostring(eview, encoding="utf-8")
        return ret_val
    
    
    def search_product_feature(self, cr, uid, ids, context=None):
        datas = self.read(cr, uid, ids, context=context)
        feature_obj = self.pool.get('feature')
        feature_ids = feature_obj.search(cr, uid, [], context=context)
        feature_records = feature_obj.browse(cr, uid, feature_ids, context=context)
        
        domain = []
        new_context = {}
        
        if datas and len(datas) == 1:
            new_context.update({
                    'search_default_feature_category': datas[0]['product_feature_category'],
                })
            context.update({
                    'feature_category': datas[0]['product_feature_category'],
                })
            domain.append(('feature_category','=',datas[0]['product_feature_category']))
            for feature_record in feature_records:
                field_name = feature_record.product_field_id.name
                if datas[0].get(field_name):
                    domain.append((field_name,'ilike',datas[0].get(field_name)))
                    
                    new_context.update({
                    'search_default_'+field_name : datas[0].get(field_name),
                })
                # Updating Context For Creating New Product    
                context.update({
                    field_name: datas[0].get(field_name),
                })
                
            product_ids = self.pool.get('product.product').search(cr, uid, domain, context=context)
            print"producr Ids>>>>>>>>>",product_ids
                    
            print"Domain>>>>>>>>>>>",domain
            if not product_ids:
                
                message = 'No Product Found With Given Search Criteria'
                product_create_wizard_id = self.pool.get('product.create.wizard').create(cr, uid, {'message':message}, context=context)
                return {
                        'name':_("Message"),
                        'view_mode': 'form',
                        'view_id': False,
                        'view_type': 'form',
                        'res_model': 'product.create.wizard',
                        'res_id': product_create_wizard_id,
                        'type': 'ir.actions.act_window',
                        'nodestroy': True,
                        'target': 'new',
                        'domain': '[]',
                        'context': context
                    }
        return {
            'name': _('Product Variants'),
            'view_type': 'form',
            'view_mode': 'tree,form,graph',
            'res_model': 'product.product',
            'view_id': False,
            'context': new_context,
            'target': 'current',
            'domain': [],
            'type': 'ir.actions.act_window',
        }
            
                
        return True
    
class product_create(osv.TransientModel):
    _name = 'product.create.wizard'
    _description = 'Product'
    
    _columns = {
            'message':fields.char('Message'),
            'name': fields.char('Product Name'),
    }
    
    def default_get(self, cr, uid, fields, context=None):
        res = {
            'message': context.get('message'),
            
        }
        return res
    
    def create_product(self, cr, uid, ids, context=None):
        print"Create Product >>>>>>",context
        current_data = self.browse(cr, uid, ids, context=context)
        feature_obj = self.pool.get('feature')
        feature_ids = feature_obj.search(cr, uid, [], context=context)
        feature_records = feature_obj.browse(cr, uid, feature_ids, context=context)
        product_vals = {'name': current_data.name or 'Test Product','feature_category':context.get('feature_category')}
        for feature_record in feature_records:
            field_name = feature_record.product_field_id.name
            for key in context.keys():
                if key == field_name and context[key] is not False:
                   product_vals.update({field_name: context[key]})
                   break
        
        
        product_id = self.pool.get('product.product').create(cr, uid, product_vals, context=context)
        return {
            'name': _('Product'),
            'view_type': 'form',
            'view_mode': 'form,tree,graph',
            'res_model': 'product.product',
            'res_id': product_id,
            'view_id': False,
            'context': context,
            #'target': 'current',
            'domain': [],
            'type': 'ir.actions.act_window',
        }
        print"Product Values>>>>>>>",product_vals
        return True


    
    
    
    
    
#https://www.odoo.com/forum/help-1/question/create-a-dynamic-list-of-checkboxes-in-a-view-1965
#http://bazaar.launchpad.net/~openerp/openobject-addons/6.0/view/head:/point_of_sale/wizard/pos_return.py
#http://pinakinnayi.blogspot.in/2013/09/dynamically-view-in-openerp.html
#http://sonuopenerp.blogspot.in/2013/08/creating-views-dynamically-in-openerp.html\
#https://aasimania.wordpress.com/2011/04/09/creating-views-dynamically/
#http://blog.openerp4you.in/2013/06/creating-views-dynamically-in-openerp.html


