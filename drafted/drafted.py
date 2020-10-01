@app.route('/chat', methods = ['GET', 'POST'])
@login_required
def chat():
    username_curr = current_user.username
    user_id = User.query.filter_by(username = username_curr).first().id
    form = MessageForm()
    
    user = User.query.all()
    diary = Diary.query.filter_by(user_id = user_id)
    
    return render_template("chat.html",diary = diary, username = username_curr,user = user,form = form)


@app.route('/chat/<username>', methods = ['GET', 'POST'])
@login_required
def send_msg(username):
   
    user = username
    sender_id = User.query.filter_by(username = user).first().id
    form = MessageForm()
    username_curr = current_user.username
    user_id = User.query.filter_by(username = username_curr).first().id
    user = User.query.all()
    diary = Diary.query.filter_by(user_id = user_id)
    messages = Message.query.order_by(Message.timestamp.asc()).all()
    message = Message.query.filter_by(sender_id = user_id or sender_id,recipient_id= sender_id or user_id)
    recieved_msg = Message.query.filter_by(recipient_id = user_id,sender_id = sender_id )
    sent_msg = Message.query.filter_by(sender_id = user_id,recipient_id = sender_id )
    return render_template("chat.html", messages = messages,user_id = user_id,diary = diary, username = username_curr,user = user,chat =1,msg=username,form = form,recieved = recieved_msg,sent = sent_msg, sender_id = sender_id )

#@socketio.on('message')
#def handleMessage(data):
 #   """Broadcast messages"""

  #  msg = data["msg"]
   # sender = data["sender"]
    #recipient = data["recipient"]
    # Set timestamp
    #send({"sender": sender,"msg": msg}, recipient=recipient,broadcast=True)
#@socketio.on('message', namespace="/msg")
#def handleMessage(data):
#    recipient = data['recipient']
#    msg = data['msg']
#    sender = data['sender']
#    request.session['_id']
#    emit('new_msg',msg,broadcast=True)
@socketio.on('incoming-msg')
def on_message(data):
    """Broadcast messages"""

    msg = data["msg"]
    username = data["username"]
    room = data["room"]
    # Set timestamp
    time_stamp = time.strftime('%b-%d %I:%M%p', time.localtime())
    emit({"username": username, "msg": msg, "time_stamp": time_stamp}, room=room)


@socketio.on('join')
def on_join(data):
    """User joins a room"""

    username = data["username"]
    room = data["room"]
    join_room(room)

    # Broadcast that new user has joined
    emit({"msg": username + " has joined the " + room + " room."}, room=room)


@socketio.on('leave')
def on_leave(data):
    """User leaves a room"""

    username = data['username']
    room = data['room']
    leave_room(room)
    emit({"msg": username + " has left the room"}, room=room)

@app.route('/chat/sendmessage/<recipient>', methods=['GET', 'POST'])
@login_required
def send_message(recipient):
    user = User.query.filter_by(username=recipient).first()
    form = MessageForm()
    
    if form.validate_on_submit():
        msg = Message(author=current_user, recipient=user,
                      body=form.message.data)
        db.session.add(msg)
        db.session.commit()
        return redirect(f'../{recipient}')
        

    return render_template('send_message.html', title=('Send Message'),form = form,
                            recipient=recipient)
@app.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    form = SearchForm()
    username_curr =  current_user.username
    diary = Diary.query.filter_by(username = username_curr)    
    return render_template('search.html',form  = form, diary = diary,username = username_curr)
  

@app.route('/search/<user>', methods=['GET', 'POST'])
@login_required
def searchRes(user):
    
    form = SearchForm()
    username = user
    search = "%{0}%".format(username)
    result = User.query.filter(User.username.like(search)).all()
    username_curr =  current_user.username
    diary = Diary.query.filter_by(username = username_curr)
    return render_template('search.html',form  = form, result= result, diary = diary,username = username_curr)
  

@app.route('/add/<username>')
@login_required
def follow_user(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('dashboard'))
    if current_user.is_following(user):
        flash('You are already following %s.' % user.username)
        return redirect(url_for('dashboard', username=username))
    current_user.follow(user)
    db.session.commit()
    flash('You are now following %s.' % user.username)
    return redirect(url_for('dashboard', username=username))
#!/var/www/html/flask/scriptapp/scriptapp-venv/bin/python3
