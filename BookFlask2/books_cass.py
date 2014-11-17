from flask import Flask, render_template, redirect, request
from cassandra.cluster import Cluster
import uuid

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


#The page to add a book to the database
@app.route('/add/', methods=['GET', 'POST'])
def add():
	if request.method == 'POST':
		new_data = {k : v for k, v in request.form.items()}
		#If the user leaves a field blank
		if new_data['title'] == '' or new_data['author'] == '' or new_data['genre'] == '' or new_data['description'] == '':
			return render_template('add.html', alert="required")
		else:
			#wrap in transaction?
			id = uuid.uuid4()
			insert_statement = "INSERT INTO "+table_name+"(id, property, value) values("+str(id)+", %s, %s)"
			session.execute(insert_statement, ('title', new_data['title']))	
			session.execute(insert_statement, ('author', new_data['author']))	
			session.execute(insert_statement, ('genre', new_data['genre']))	
			session.execute(insert_statement, ('description', new_data['description']))			
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

		title_dict = {}
		for row in title_ids:
			id = row.id
			title_name = session.execute(value_select_statement, (id, 'title'))[0]
			author_name = session.execute(value_select_statement, (id, 'author'))[0]  
			inner_dict = {'title': title_name.value, 'author': author_name.value}
			title_dict[str(id)] = inner_dict

		author_dict = {}
		for row in author_ids:
			id = row.id
			title_name = session.execute(value_select_statement, (id, 'title'))[0]
			author_name = session.execute(value_select_statement, (id, 'author'))[0]  
			inner_dict = {'title': title_name.value, 'author': author_name.value}
			author_dict[str(id)] = inner_dict


		print(title_dict)
		print(author_dict)

		return render_template('search_cass.html', posting=True, query=query, title_results=title_dict, author_results=author_dict)  

	else:
		return render_template('search_cass.html', posting=False)


#Individual information page for each book
@app.route('/detail/<id>/', methods=['GET', 'POST'])
def detail(id):
	id = uuid.UUID(id)
	if request.method == 'POST':
		#In the dict request.form, pre-existing properties and values make up key-value pairs, with the property being the key and the value being the value. New properties and values are all values in the dictionary, and their keys are named "new_field"+str(pair_number) and "new_value"+str(pair_number), respectively. pair_number is a digit that identifies which new property goes with which new value. 	
		for key, value in request.form.iteritems():
			#add new property and value to book
			if key[:9] == 'new_field':
				pair_number = key[9:]
				session.execute("UPDATE "+table_name+" SET value = %s WHERE id = %s and property = %s",(request.form['new_value'+str(pair_number)], id, value))			
			#update value of existing property of book
			elif key[:9] != 'new_value':
				session.execute("UPDATE "+table_name+" SET value = %s WHERE id = %s and property = %s",(value, id, key))

	result = {}
	all_properties = session.execute("SELECT property, value FROM "+table_name+" WHERE id = %s", (id,)) 
	for property in all_properties:
		result[property.property] = property.value
	return render_template('detail_cass.html', result=result, id=id)




def convert_to_dict(iterable, *fields):
	outer_dict = {}
	outer_key = 0
	for element in iterable:
		inner_dict = {}
		for field in fields:
			inner_dict[field] = getattr(element, field)
		outer_dict[outer_key]= inner_dict
		outer_key += 1
	return outer_dict




if __name__ == '__main__':
	app.debug = True
	app.run()



