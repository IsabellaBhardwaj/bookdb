from flask import Flask, render_template, redirect, request
# import pymongo

app = Flask(__name__, static_url_path = "")
user = 'C##BOOKS'
model = 'Book'
conn = connectTo 'jdbc:oracle:thin:@129.152.144.84:1521:orcl' 'C##BOOKS' 'orcl_books' 'rdf_mode' 'Book';
conn2 = connectTo 'jdbc:oracle:thin:@129.152.144.84:1521:orcl' 'C##BOOKS' 'orcl_books' 'native_mode' 'Book';

#Homepage
@app.route('/')
def splash():
	return app.send_static_file('splash.html')

#Remove a book
@app.route('/remove/<title>/<author>/')
def remove(title, author):
    subject = SQL on conn2 """SELECT s1
			 FROM TABLE(SEM_MATCH('SELECT * WHERE {
				?s1 rdf:type :books .
				OPTIONAL { ?s1 :title ?v1 }
				OPTIONAL { ?s1 :author ?v2 }
				?s1 :title ?f1 .
				FILTER(?f1 = "t1") }' ,
			SEM_MODELS('BOOK_C##BOOKS'), null,
			SEM_ALIASES( SEM_ALIAS('', 'http://www.example.org/people.owl#')), null) ) """

    SQL on conn2 """DELETE FROM BOOK_C##BOOKS_DATA a 
            WHERE a.triple.get_subject()  = '<"""subject[1][0]""">'"""
    return redirect('/')

#Individual information page for each book
@app.route('/detail/<title>/<author>/', methods=['GET', 'POST'])
def display(title, author):
	if request.method == 'GET':
		results = SQL on conn """select * from books where title = '"""title"""' and author = '"""author"""'"""
		result_dict = {}
		num = 0
		for r in results[1] :
		   if results[0][num] != 'DBUNIQUEID' :
		      result_dict.update({results[0][num] : r})
		   num += 1
	elif request.method == 'POST':
	    return update(title, author)
	return render_template('detail.html', result=result_dict, js_results=result_dict)

#Update a book's fields and attributes
def update(title, author):
	subject = SQL on conn2 """SELECT s1
			 FROM TABLE(SEM_MATCH('SELECT * WHERE {
				?s1 rdf:type :books .
				OPTIONAL { ?s1 :title ?v1 }
				OPTIONAL { ?s1 :author ?v2 }
				?s1 :title ?f1 .
				?s1 :author ?f2 .
				FILTER(?f1 = \""""title"""\" && ?f2 = \""""author"""\") }' ,
			SEM_MODELS('BOOK_C##BOOKS'), null,
			SEM_ALIASES( SEM_ALIAS('', 'http://www.example.org/people.owl#')), null) ) """

# Add new values of all pre-existing attributes
	results = SQL on conn """select * from books where title = '"""title"""' and author = '"""author"""'"""
	result_dict = {}
	num = 0
	for r in results[1] :
		if results[0][num] != 'DBUNIQUEID' :
		   result_dict.update({results[0][num] : r})
		num += 1
	updated_dict = {attribute: value for attribute, value in request.form.iteritems() if attribute[:14] != '__new__field__' and attribute[:14] != '__new__value__'}
	changes_dict = dict([(k, updated_dict.get(k)) for k in updated_dict if updated_dict.get(k) not in result_dict.values()])
	removes_dict = dict([(k, result_dict.get(k)) for k in result_dict if result_dict.get(k) not in updated_dict.values()])
	print 'result_dict ***************************************************************', result_dict
	print 'updated_dict ***************************************************************', updated_dict
	print 'changes_dict ***************************************************************', changes_dict
	print 'removes_dict ***************************************************************', removes_dict
	for k in changes_dict :
	   do_update(subject, k, result_dict.get(k), changes_dict.get(k))

# Add values of new fields, if any
	num_old_fields = len(updated_dict)
	num_new_fields = (len(request.form)-num_old_fields)/2
	if(num_new_fields > 0) :
		for i in range(1, num_new_fields + 1):
			new_attribute = request.form['__new__field__'+str(i)]
			new_value = request.form['__new__value__'+str(i)]
			# updated_dict[new_attribute] = new_value
			print subject[1][0], new_attribute, new_value
			do_insert(subject, new_attribute, new_value)
			
# Remove selected attributes, if any
	for k in removes_dict :
	   do_remove(subject, k, removes_dict.get(k))
			
# Return new results
	results = SQL on conn """select * from books where title = '"""title"""' and author = '"""author"""'"""
	result_dict = {}
	num = 0
	for r in results[1] :
	   if results[0][num] != 'DBUNIQUEID' :
	      result_dict.update({results[0][num] : r})
	   num += 1
	return render_template('detail.html', result=result_dict, js_results=result_dict)

def do_insert(subject, attr, value):
	SQL on conn2 """INSERT INTO BOOK_C##BOOKS_DATA VALUES ( BOOK_C##BOOKS_SQNC.nextval, SDO_RDF_TRIPLE_S('BOOK_C##BOOKS:<http://www.example.org/people.owl>', '"""subject[1][0]"""', 'http://www.example.org/people.owl#"""attr"""', '\""""value"""\"^^<http://www.w3.org/2001/XMLSchema#string>'))"""
	SQL on conn2 """INSERT INTO BOOK_C##BOOKS_DATA VALUES ( BOOK_C##BOOKS_SQNC.nextval, SDO_RDF_TRIPLE_S('BOOK_C##BOOKS:<http://www.example.org/people.owl>', 'http://www.example.org/people.owl#"""attr"""', 'rdf:type', 'owl:DatatypeProperty'))"""
	SQL on conn2 """INSERT INTO BOOK_C##BOOKS_DATA VALUES ( BOOK_C##BOOKS_SQNC.nextval, SDO_RDF_TRIPLE_S('BOOK_C##BOOKS:<http://www.example.org/people.owl>', 'http://www.example.org/people.owl#"""attr"""', 'rdfs:domain', 'http://www.example.org/people.owl#books'))"""
	SQL on conn2 """INSERT INTO BOOK_C##BOOKS_DATA VALUES ( BOOK_C##BOOKS_SQNC.nextval, SDO_RDF_TRIPLE_S('BOOK_C##BOOKS:<http://www.example.org/people.owl>', 'http://www.example.org/people.owl#"""attr"""', 'rdf:range', 'rdfs:xsd:string'))"""
	SQL on conn2 """INSERT INTO BOOK_C##BOOKS_DATA VALUES ( BOOK_C##BOOKS_SQNC.nextval, SDO_RDF_TRIPLE_S('BOOK_C##BOOKS:<http://www.example.org/people.owl>', 'http://www.example.org/people.owl#"""attr"""', 'rdf:type', 'owl:FunctionalProperty'))"""

def do_update(subject, attr, old_value, new_value):
	SQL on conn2 """UPDATE BOOK_C##BOOKS_DATA a
	SET a.triple = SDO_RDF_TRIPLE_S(
	'BOOK_C##BOOKS', a.triple.get_subject(),
	'<http://www.example.org/people.owl#"""attr""">',
	'\""""new_value"""\"^^<http://www.w3.org/2001/XMLSchema#string>')
	WHERE a.triple.get_subject()  = '<"""subject[1][0]""">'
	  AND a.triple.get_property()  = '<http://www.example.org/people.owl#"""attr""">'
	  AND a.triple.get_obj_value() = '\""""old_value"""\"^^<http://www.w3.org/2001/XMLSchema#string>'"""
	  
def do_remove(subject, attr, value):
    SQL on conn2 """DELETE FROM BOOK_C##BOOKS_DATA a 
			  WHERE a.triple.get_subject()  = '<"""subject[1][0]""">'
			  AND a.triple.get_property()  = '<http://www.example.org/people.owl#"""attr""">'
			  AND a.triple.get_obj_value() = '\""""value"""\"^^<http://www.w3.org/2001/XMLSchema#string>'"""

#serves image in image file for a particular book
@app.route('/static/images/<image>/')
def image(image):
	return app.send_static_file('images/'+image)

#The search page
@app.route('/search/', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        query = request.form['query']
        
        titles = SQL on conn """select title, author from books where title = '"""query"""'"""
        authors = SQL on conn """select title, author from books where author = '"""query"""'"""
        result_dict = {}
        num = 0
        for j in titles :
            result_dict.update({'Key' + str(num) : {'title' : j[0], 'author' : j[1]}})
            num += 1
        num = 0
        for j in authors :
            result_dict.update({'Key' + str(num) : {'title' : j[0], 'author' : j[1]}})
            num += 1

        no_results = result_dict == 0
        return render_template('search.html', posting=True, query=query, no_results=no_results, results=result_dict) 
    else:
		return render_template('search.html', posting=False)

#The page to add a book to the database
@app.route('/add/', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        new_data = {k : v for k, v in request.form.items()}
        #If the user leaves a field blank
        if new_data['title'] == '' or new_data['author'] == '' or new_data['genre'] == '' or new_data['description'] == '':
            return render_template('add.html', alert="required")
        else:
            values = (str(new_data['title']), str(new_data['author']), str(new_data['genre']), str(new_data['description']))
            SQL on conn """insert into books(title, author, genre, description) values"""values
            return render_template('add.html', alert = "success")
    else:
        return render_template('add.html', alert="")

if __name__ == '__main__':
	app.debug = True
	app.run()



