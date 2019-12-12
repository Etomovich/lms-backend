from lms_app import create_app

app = create_app()
app_context = app.app_context()
app_context.push()

if __name__ == '__main__':
    app.run(debug=True)
