from flask import Flask, render_template, redirect, request
import pymongo


app = Flask(__name__, static_url_path = "")
connection_string = "mongodb://127.0.0.1"
connection = pymongo.MongoClient(connection_string)
database = connection.books
books = database.mybooks

#Homepage
@app.route('/')
def splash():
	return app.send_static_file('splash.html')


#Remove a book
@app.route('/remove/<title>/<author>/')
def remove(title, author):
	books.remove({'title':title, 'author':author})
	return redirect('/')

#Individual information page for each book
@app.route('/detail/<title>/<author>/', methods=['GET'])
def display(title, author):

	cursor = books.find_one({'title':title, 'author':author})
	results = {field: value for field, value in cursor.items()}
	js_results = {str(field).replace('"', '\\"') :str(value).replace('"', '\\"') for field, value in results.items()}
	return render_template('detail.html', result=results, js_results=js_results)


#Update a book's fields and attributes
@app.route('/detail/<title>/<author>/', methods=['POST'])
def update(title, author):

	#Add new values of all pre-existing attributes
	updated_document = {attribute: value for attribute, value in request.form.iteritems() if attribute[:14] != '__new__field__' and attribute[:14] != '__new__value__'}
	num_old_fields = len(updated_document)
	num_new_fields = (len(request.form)-num_old_fields)/2
	#Add values of new fields, if any
	if(num_new_fields > 0):
		for i in range(1, num_new_fields + 1):
			new_attribute = request.form['__new__field__'+str(i)]
			new_value = request.form['__new__value__'+str(i)]
			updated_document[new_attribute] = new_value

	books.update({'title':title, 'author': author}, updated_document)
	cursor = books.find_one({'title': request.form['title'], 'author': request.form['author']})
	results = {field: value for field, value in cursor.items()}
	js_results = {str(field).replace('"', '\\"') :str(value).replace('"', '\\"') for field, value in results.items()}
	return render_template('detail.html', result=results, js_results=js_results)



#serves image in image file for a particular book
@app.route('/static/images/<image>/')
def image(image):
	return app.send_static_file('images/'+image)


#The search page
@app.route('/search/', methods=['GET', 'POST'])
def search():
	#Return results for titles, authors and genres that match the search query
	if request.method == 'POST':
		query = request.form['query']
		
		result_cursor = books.find({'$or':[{'title':query},{'author':query}]})

		no_results = result_cursor.count() == 0
	
		result_dict = convert_to_dict(result_cursor)     

		return render_template('search.html', posting=True, query=query, no_results=no_results, results=result_dict)  
	else:
		return render_template('search.html', posting=False)


def convert_to_dict(iterable):
	outer_dict = {}
	for element in iterable:
		inner_dict = {} 
		for key in element:
			inner_dict[key] = element[key]	
		outer_dict[element['_id']]= inner_dict
	return outer_dict


#The page to add a book to the database
@app.route('/add/', methods=['GET', 'POST'])
def add():
	if request.method == 'POST':
		new_data = {k : v for k, v in request.form.items()}
		#If the user leaves a field blank
		if new_data['title'] == '' or new_data['author'] == '' or new_data['genre'] == '' or new_data['description'] == '':
			return render_template('add.html', alert="required")
		#If the user tries to add a book that's already in the database
		elif books.find({'title':new_data['title'], 'author':new_data['author']}).count() > 0: 
			return render_template('add.html', alert="exists")
		else:
			books.insert(new_data)
			return render_template('add.html', alert = "success")
	else:
		return render_template('add.html', alert="")

if __name__ == '__main__':
	app.debug = True
	app.run()



