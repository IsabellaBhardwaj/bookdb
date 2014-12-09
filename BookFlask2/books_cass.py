from flask import Flask, render_template, redirect, request
from cassandra.cluster import Cluster
import uuid
from cassandra.query import BatchStatement


app = Flask(__name__, static_url_path = "")

cluster = Cluster()
session = cluster.connect('keyspace1')

table_name = "time_exp4"

session.execute("CREATE TABLE IF NOT EXISTS %s(id uuid, property text, value text, primary key(id, property));"%table_name)

session.execute("CREATE INDEX IF NOT EXISTS on %s(value);"%table_name)

#Homepage
@app.route('/')
def splash():
	return app.send_static_file('splash.html')

#Remove a book from the database
@app.route('/remove/<id>/')
def remove(id):
	id = uuid.UUID(id)
	delete_statement = "DELETE FROM "+table_name+" WHERE id=%s"
	session.execute(delete_statement, (id,))
	return redirect('/')

#The page to add a book to the database
@app.route('/add/', methods=['GET', 'POST'])
def add():
	if request.method == 'POST':
		new_data = {k : v for k, v in request.form.items()}
		#If the user leaves a field blank
		if new_data['title'] == '' or new_data['author'] == '' or new_data['genre'] == '' or new_data['description'] == '':
			return render_template('add.html', alert="required")
		else:
			id = uuid.uuid4()
			batch = BatchStatement()
			insert_statement = "INSERT INTO "+table_name+"(id, property, value) values("+str(id)+", %s, %s)"
			batch.add(insert_statement, ('title', new_data['title']))	
			batch.add(insert_statement, ('author', new_data['author']))	
			batch.add(insert_statement, ('genre', new_data['genre']))	
			batch.add(insert_statement, ('description', new_data['description']))
			session.execute(batch)			
			return render_template('add.html', alert = "success")
	else:
		return render_template('add.html', alert="")


#The search page
@app.route('/search/', methods=['GET', 'POST'])
def search():
	#Return results for titles, authors and genres that match the search query
	if request.method == 'POST':
		query = request.form['query']
		
		id_select_statement = "SELECT id FROM "+table_name+" WHERE property = %s and value = %s ALLOW FILTERING"

		title_ids = session.execute(id_select_statement, ('title', query))

		author_ids = session.execute(id_select_statement, ('author', query))

		value_select_statement = "SELECT value FROM "+table_name+" WHERE id = %s and property = %s LIMIT 1 ALLOW FILTERING"

		result_dict = {}
		for row in title_ids:
			id = row.id
			title_name = session.execute(value_select_statement, (id, 'title'))[0]
			author_name = session.execute(value_select_statement, (id, 'author'))[0]  
			inner_dict = {'title': title_name.value, 'author': author_name.value}
			result_dict[str(id)] = inner_dict

		for row in author_ids:
			id = row.id
			title_name = session.execute(value_select_statement, (id, 'title'))[0]
			author_name = session.execute(value_select_statement, (id, 'author'))[0]  
			inner_dict = {'title': title_name.value, 'author': author_name.value}
			result_dict[str(id)] = inner_dict


		return render_template('search_cass.html', posting=True, query=query, results=result_dict)  

	else:
		return render_template('search_cass.html', posting=False)


#Update information for a book
def update(id):

	old_prop_query = "SELECT property FROM "+table_name+" WHERE id=%s"
	old_rows = session.execute(old_prop_query, (id,))
	#all properties for this book prior to upgrade
	old_properties = {str(row.property) for row in old_rows}
	#all properties for this book after upgrade
	current_properties = set()

	#In the dict request.form, pre-existing properties and values make up key-value pairs, with the property being the key and the value being the value. New properties and values are all values in the dictionary, and their keys are named "__new__field__"+str(pair_number) and "__new__value__"+str(pair_number), respectively. pair_number is a digit that identifies which new property goes with which new value. 	
	batch = BatchStatement()
	for key, value in request.form.iteritems():
		#add new property and value to book
		if key[:14] == '__new__field__':
			pair_number = key[14:]
			batch.add("UPDATE "+table_name+" SET value = %s WHERE id = %s and property = %s",(request.form['__new__value__'+str(pair_number)], id, value))			
			current_properties.add(str(value))
			
		#update value of existing property of book
		elif key[:14] != '__new__value__':
			batch.add("UPDATE "+table_name+" SET value = %s WHERE id = %s and property = %s",(value, id, key))
			current_properties.add(str(key)) 
		
	to_remove = old_properties - current_properties
	delete_statement = "DELETE FROM "+table_name+" WHERE id=%s and property=%s"
	for property in to_remove:
		batch.add(delete_statement, (id, property)) 
	session.execute(batch)

#Update information for a book
@app.route('/detail/<id>/', methods=['GET', 'POST'])
def display(id):

	id = uuid.UUID(id)
	if request.method == 'POST':
		update(id)
	
	results = {}
	all_props_and_vals = session.execute("SELECT property, value FROM "+table_name+" WHERE id = %s", (id,)) 
	for property in all_props_and_vals:
		results[property.property] = property.value
	js_results = {str(field).replace('"', '\\"') :str(value).replace('"', '\\"') for field, value in results.items()}
	return render_template('detail_cass.html', result=results, js_results=js_results, id=id)

	

if __name__ == '__main__':
	app.debug = True
	app.run()



