import logging

from flask_admin.model import BaseModelView
from wtforms_appengine import db as wt_db
from wtforms_appengine import ndb as wt_ndb

from google.appengine.ext import db
from google.appengine.ext import ndb

class NdbModelView(BaseModelView):
	"""
	AppEngine NDB model scaffolding.
	"""

	def get_pk_value(self, model):
		return model.key.urlsafe()

	def scaffold_list_columns(self):
		return sorted([k for (k, v) in self.model.__dict__.iteritems() if isinstance(v, ndb.Property)])

	def scaffold_sortable_columns(self):
		return [k for (k, v) in self.model.__dict__.iteritems() if isinstance(v, ndb.Property) and v._indexed]

	def init_search(self):
		return None

	def is_valid_filter(self):
		pass

	def scaffold_filters(self):
		#TODO: implement
		pass

	def scaffold_form(self):
		return wt_ndb.model_form(self.model())

	def get_list(self, page, sort_field, sort_desc, search, filters):
		#TODO: implement filters (don't think search can work here)

		q = self.model.query()

		if sort_field:
			order_field = getattr(self.model, sort_field)
			if sort_desc:
				order_field = -order_field
			q = q.order(order_field)

		results = q.fetch(self.page_size, offset=page*self.page_size)
		return q.count(), results

	def get_one(self, urlsafe_key):
		return ndb.Key(urlsafe=urlsafe_key).get()

	def create_model(self, form):
		try:
			model = self.model()
			form.populate_obj(model)
			model.put()
			return model
		except Exception as ex:
			if not self.handle_view_exception(ex):
				#flash(gettext('Failed to create record. %(error)s',
				#	error=ex), 'error')
				logging.exception('Failed to create record.')
			return False

	def update_model(self, form, model):
		try:
			form.populate_obj(model)
			model.put()
			return True
		except Exception as ex:
			if not self.handle_view_exception(ex):
				#flash(gettext('Failed to update record. %(error)s',
				#	error=ex), 'error')
				logging.exception('Failed to update record.')
			return False

	def delete_model(self,  model):
		try:
			model.key.delete()
			return True
		except Exception as ex:
			if not self.handle_view_exception(ex):
				#flash(gettext('Failed to delete record. %(error)s',
				#	error=ex),
				#	'error')
				logging.exception('Failed to delete record.')
		return False


class DbModelView(BaseModelView):
	"""
	AppEngine DB model scaffolding.
	"""

	def get_pk_value(self, model):
		return str(model.key())

	def scaffold_list_columns(self):
		return sorted([k for (k, v) in self.model.__dict__.iteritems() if isinstance(v, db.Property)])

	def scaffold_sortable_columns(self):
		return [k for (k, v) in self.model.__dict__.iteritems() if isinstance(v, db.Property) and v._indexed]

	def init_search(self):
		return None

	def is_valid_filter(self):
		pass

	def scaffold_filters(self):
		#TODO: implement
		pass

	def scaffold_form(self):
		return wt_db.model_form(self.model())

	def get_list(self, page, sort_field, sort_desc, search, filters):
		#TODO: implement filters (don't think search can work here)

		q = self.model.all()

		if sort_field:
			if sort_desc:
				sort_field = "-" + sort_field
			q.order(sort_field)

		results = q.fetch(self.page_size, offset=page*self.page_size)
		return q.count(), results

	def get_one(self, encoded_key):
		return db.get(db.Key(encoded=encoded_key))

	def create_model(self, form):
		try:
			model = self.model()
			form.populate_obj(model)
			model.put()
			return model
		except Exception as ex:
			if not self.handle_view_exception(ex):
				#flash(gettext('Failed to create record. %(error)s',
				#	error=ex), 'error')
				logging.exception('Failed to create record.')
			return False

	def update_model(self, form, model):
		try:
			form.populate_obj(model)
			model.put()
			return True
		except Exception as ex:
			if not self.handle_view_exception(ex):
				#flash(gettext('Failed to update record. %(error)s',
				#	error=ex), 'error')
				logging.exception('Failed to update record.')
			return False

	def delete_model(self,  model):
		try:
			model.delete()
			return True
		except Exception as ex:
			if not self.handle_view_exception(ex):
				#flash(gettext('Failed to delete record. %(error)s',
				#	error=ex),
				#	'error')
				logging.exception('Failed to delete record.')
		return False

def ModelView(model):
	if issubclass(model, ndb.Model):
		return NdbModelView(model)
	elif issubclass(model, db.Model):
		return DbModelView(model)
	else:
		raise ValueError("Unsupported model: %s" % model)
