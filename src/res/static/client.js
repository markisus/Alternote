var client = {};
(function() {
	var rts_address = "http://localhost:8888";
	client.initialize = function(eventid, userid) {
		client.eventid = eventid;
		client.userid = userid;
		client.get();
		console.log("Initialized.");
	};
	
	var nonce = 0;
	
	client.injectScript = function(src) {
		var _inject = function(src) {
			console.log("Injecting " + src);
			nonce++;
			var div = document.getElementById('scriptInject');
			var script = document.createElement('script');
			script.setAttribute('type', 'text/javascript');
			script.setAttribute('src', rts_address + src + '?' + nonce);
			div.appendChild(script);
		};
		window.setTimeout(_inject, 0, src);
	}
	
	client.callback = function(data) {
		console.log("callback...");
		for (key in data) {
			if (key > client.last_element) client.last_element = key;
			var data_piece = data[key];
			var action = data_piece['action'];
			eval("client.x" + action + "(data_piece)");
		}
		//Callback means the long poll has finished. Restart the listener
		client.listen();
	};
	
	client.get = function() {
		console.log(client.eventid);
		client.injectScript("/get/" + client.eventid);
	};
	
	client.listen = function() {
		console.log("Listening...");
		client.injectScript("/poll/" + client.eventid + "/" + client.last_element);
	}
	
	client.vote = function(objectid) {
		client.injectScript("/vote/" + objectid);
	};
	
	client.unvote = function(objectid) {
		client.injectScript("/unvote/" + objectid);
	};
	
	client.flag = function(objectid) {
		client.injectScript("/flag/" + objectid);
	};
	
	client.unflag = function(objectid) {
		client.injectScript("/unflag/" + objectid);
	};
	
	client.post = function(message) {
		_post_helper("post", client.eventid, message);
	}
	
	client.anon_post = function(message) {
		_post_helper("anon_post", client.eventid, message);
	}
	
	client.comment = function(parentid, message) {
		_post_helper("comment", parentid, message);
	}
	
	client.anon_comment = function(parentid, message) {
		_post_helper("anon_comment", parentid, message);
	}
	
	/* I think this code below was an accident. keeping it around to be safe
	client.anon_post = function(message) {
		client.injectScript("/anon_post/" + client.eventid + "/" + message);
	}*/
	
	var _post_helper = function(api_call, parentid, message) {
		message = escape(message);
		client.injectScript("/" + api_call + "/" + parentid + "/" + message);
	}
	
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
	}

	var _render_post = function(objectid, author, message, votes, flags) {
		_render_helper('posts', 'post', objectid, author, message, votes, flags);
	}
	
	var _render_comment = function(parent, objectid, author, message, votes, flags) {
		_render_helper(parent, 'comment', objectid, author, message, votes, flags);
	}
	
	//Actions will be called from client.callback
	client.xget = function(data) {
		console.log("xget");
		client.last_element = data['last_element'];
		client.votes_and_flags = data['votes_and_flags'];
		var posts = data['posts'];
		console.log(posts);
		for (key in posts) {
			var post = posts[key];
			_render_post(post['_id'], post['author'], post['message'], post['votes'], post['flags']);
			for (ckey in post['comments']) {
				var comment = post['comments'][ckey];
				_render_comment(comment['_id'], comment['author'], comment['message'], comment['votes'], comment['flags']);
			}
		}
		console.log(data);
	};
	
	client.xvote = function(data) {
		console.log(data);
	}
	
	client.xunvote = function(data) {
		console.log(data);
	}
	
	client.xflag = function(data) {
		console.log(data);
	}
	
	client.xunflag = function(data) {
		console.log(data);
	}
	
	client.xpost = function(data) {
		_render_post(data['objectid'], data['user'], data['message'], 0, 0);
	}
	
	client.xcomment = function(data) {
		console.log(data);
		_render_comment(data['postid'], data['objectid'], data['user'], data['message'], 0, 0);
	}
})();