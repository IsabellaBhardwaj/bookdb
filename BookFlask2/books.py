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
    return render_template('detail.html', result=books.find_one({'title':title, 'author':author}))

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
        return render_template('search.html', posting=True, query=query, title_results = books.find({'title':query}),
                               author_results = books.find({'author':query}), genre_results = books.find({'genre':query}))  
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



