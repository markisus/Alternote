//var client = {};
function Client(eventid, userid, messages) {
	var self = this;
	console.log("Inside client");
	
	var rts_address = "http://localhost:8888";
	self.initialize = function(eventid, userid, messages) {
		console.log(eventid, userid);
		self.eventid = eventid;
		self.userid = userid;
		self.messages = messages;
		self.get();
		console.log("Initialized.");
	};
	
	var nonce = 0;
	
	self.injectScript = function(src) {
		var _inject = function(src) {
			console.log("Injecting " + src);
			nonce++;
			var div = document.getElementById('scriptInject');
			console.log(div);
			var script = document.createElement('script');
			script.setAttribute('type', 'text/javascript');
			script.setAttribute('src', rts_address + src + '?' + nonce);
			div.appendChild(script);
		};
		window.setTimeout(_inject, 100, src);
	};
	
	self.callback = function(data) {
		console.log("callback...");
		for (key in data) {
			if (parseInt(key) > parseInt(self.last_element)) self.last_element = parseInt(key);
			var data_piece = data[key];
			var action = data_piece['action'];
			eval("self.x" + action + "(data_piece)");
		}
		//Callback means the long poll has finished. Restart the listener
		self.listen();
	};
	
	self.get = function() {
		console.log(self.eventid);
		self.injectScript("/get/" + self.eventid);
	};
	
	self.listen = function() {
		console.log("Listening...");
		self.injectScript("/poll/" + self.eventid + "/" + self.last_element);
	};
	
	self.vote = function(objectid) {
		self.injectScript("/vote/" + objectid);
	};
	
	self.unvote = function(objectid) {
		self.injectScript("/unvote/" + objectid);
	};
	
	self.flag = function(objectid) {
		self.injectScript("/flag/" + objectid);
	};
	
	self.unflag = function(objectid) {
		self.injectScript("/unflag/" + objectid);
	};
	
	self.post = function(message) {
		_post_helper("post", self.eventid, message);
	};
	
	self.anon_post = function(message) {
		_post_helper("anon_post", self.eventid, message);
	};
	
	self.comment = function(parentid, message) {
		_post_helper("comment", parentid, message);
	};
	
	self.anon_comment = function(parentid, message) {
		_post_helper("anon_comment", parentid, message);
	};
	
	
	var _post_helper = function(api_call, parentid, message) {
		message = escape(message);
		self.injectScript("/" + api_call + "/" + parentid + "/" + message);
	};
	
	var _render_helper = function(parent, objecttype, objectid, author, message, votes, flags) {
		data = {
			objectid: objectid,
			objecttype: objecttype,
			author: author['first_name'] + " " + author['last_name'],
			authorimg: 'x',
			message: message,
			votes: "" + votes,
			flags: "" + flags,
		};
		$('#' + parent).append( $('#object').render(data));
	};

	var _render_post = function(objectid, author, message, votes, flags) {
		_render_helper('posts', 'post', objectid, author, message, votes, flags);
	};
	
	var _render_comment = function(parent, objectid, author, message, votes, flags) {
		_render_helper(parent, 'comment', objectid, author, message, votes, flags);
	};
	
	//Actions will be called from self.callback
	self.xget = function(data) {
		console.log("xget");
		self.last_element = data['last_element'];
		self.votes_and_flags = data['votes_and_flags'];
		var posts = data['posts'];
		console.log(posts);
		/*
		for (key in posts) {
			var post = posts[key];
			_render_post(post['_id'], post['author'], post['message'], post['votes'], post['flags']);
			for (ckey in post['comments']) {
				var comment = post['comments'][ckey];
				_render_comment(comment['_id'], comment['author'], comment['message'], comment['votes'], comment['flags']);
			}
		}*/
		_(posts).forEach(function(item){
			self.messages.add(item);
		});
		
	};
	
	self.xvote = function(data) {
		console.log(data);
		var id = data['objectid'];
		var action_id = data['userid'];
		
		var votes = self.messages.get(id).get("votes");
		self.messages.get(id).set("votes", votes+1);
		if (action_id == self.userid) {
			self.messages.get(id).trigger("toggle_vote")
		}
		console.log(data);
	};
	
	self.xunvote = function(data) {
		console.log(data);
		var id = data['objectid'];
		var action_id = data['userid'];
		
		var votes = self.messages.get(id).get("votes");
		self.messages.get(id).set("votes", votes-1);
		if (action_id == self.userid) {
			self.messages.get(id).trigger("toggle_vote");
		}
		console.log(data);
	};
	
	self.xflag = function(data) {
		var id = data['objectid'];
		var action_id = data['userid'];
		
		var flags = self.messages.get(id).get("flags");
		self.messages.get(id).set("flags", flags+1);
		if (action_id == self.userid) {
			self.messages.get(id).trigger("toggle_flag")
		}
		console.log(data);
	};
	
	self.xunflag = function(data) {
		console.log(data);
		var id = data['objectid'];
		var action_id = data['userid'];
		
		var flags = self.messages.get(id).get("flags");
		self.messages.get(id).set("flags", flags-1);
		if (action_id == self.userid) {
			self.messages.get(id).trigger("toggle_flag")
		}
		console.log(data);
	};
	
	self.xpost = function(data) {
		self.messages.add(
				{'id':data['objectid'], 
				'event_id':self.eventid,
				'author':data['user'], 
				'message':data['message'], 
				'votes':0, 
				'flags':0,
				'parent_id':null,
				'timestamp':data['timestamp']
				}
		);
	};
	
	self.xcomment = function(data) {
		console.log(data);
		self.messages.add(
				{'id':data['objectid'], 
				'event_id':self.eventid,
				'author':data['user'], 
				'message':data['message'], 
				'votes':0, 
				'flags':0,
				'parent_id':data['parent_id'],
				'timestamp':data['timestamp']
				}
		);
	};
	
	console.log("initializing");
	self.initialize(eventid, userid, messages);
};