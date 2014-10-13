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

#Individual information page for each book
@app.route('/detail/<title>/<author>/')
def detail(title, author):
	cursor = books.find_one({'title':title, 'author':author})
	results = {field:value for field, value in cursor.items()}
	return render_template('detail.html', result=results)

#serves image in image file for a particular book
@app.route('/static/images/<image>/')
def image(image):
	return app.send_static_file('images/'+image)

#Leads to detail page of a randomly chosen book
@app.route('/featured/')
def featured():
	random = books.find_one()
	return redirect('/detail/'+random['title']+'/'+random['author']+'/')


#The search page
@app.route('/search/', methods=['GET', 'POST'])
def search():
	#Return results for titles, authors and genres that match the search query
	if request.method == 'POST':
		query = request.form['query']
		title_cursor = books.find({'title':query})
		author_cursor = books.find({'author':query})

		no_results = author_cursor.count() == 0 and title_cursor.count() == 0
	
		title_dict = convert_to_dict(title_cursor)
		author_dict = convert_to_dict(author_cursor)     

		return render_template('search.html', posting=True, query=query, no_results=no_results, title_results=title_dict, author_results=author_dict, genre_results={})  
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



