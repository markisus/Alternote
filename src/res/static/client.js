console.log("client.js start");
var client = {};
(function() {
	client.init = function(eventid, userid) {
		client.eventid = eventid;
		client.userid = userid;
		console.log("Asking for posts for eventid " + eventid);
		$.getJSON("/get/" + eventid + "/", function(data) {
			client.posts = data.posts;
			client.last_element = data.last_element;
			client.voted = data.votes_and_flags.voted;
			client.flagged = data.votes_and_flags.flagged;
			//Generate HTML on the fly
			for (post_index in data.posts) {
				var post = data.posts[post_index];
				var postid = post['_id'];
				var message = post['post']; //Todo: this is sometimes called 'message' which is inconsistent
				var flags = post['flags'];
				var votes = post['votes'];
				var author_data = post['author'];
				add_post_tag(postid, message, flags, votes, author_data);
				
				var comments = post['comments'];
				for (comment_index in comments) {
					var comment = comments[comment_index];
					var commentid = comment['_id'];
					var message = comment['comment'];
					var flags = comment['flags'];
					var votes = comment['votes'];
					var author_data = comment['author'];
					console.log(post);
					console.log(comment);
					console.log("Calling add comment tag " + message);
					add_comment_tag(postid, commentid, message, flags, votes, author_data);
				}
			}
			console.log(client);
			//Do not move the call to listen outside of the callback
			//You risk calling listen when client is in inconsistent state
			client.listen();
		});
	};
	
	client.listen = function(data) {
		if(data) synchronize(data);
		$.getJSON("/poll/" + client.eventid + "/" + client.last_element, client.listen);
	}
	
	//Server will give us a list of updates,
	//Apply each update to maintain consistency with the server
	var synchronize = function(actions) {
		var counter = 0;
		for(index in actions) {
			apply_action(actions[index]);
			counter += 1;
		}
		client.last_element += counter;
	};
	
	var apply_action = function(action) {
		//The action could be one of 10 cases
			//comment
			//post
			//flag post|comment
			//unflag post|comment
			//vote post|comment
			//unflag post|comment
		if (action['action'] === 'post') {
			var postid = action['postid'];
			var message = action['message'];
			var flags = 0;
			var votes = 0;
			var author_data = action['user'];
			add_post_tag(postid, message, flags, votes, author_data);
		}
		if (action['action'] === 'comment') {
			var postid = action['postid'];
			var commentid = action['commentid'];
			var message = action['message'];
			var flags = 0;
			var votes = 0;
			var author_data = action['user'];
			add_comment_tag(postid, commentid, message, flags, votes, author_data);
		}
		if (action['action'] === 'vote_post') {
			var postid = action['postid'];
			var userid = action['userid'];
			if (userid === client.userid) {
				disable_vote(postid);
			}
			var votes = $('#' + postid + "> .stats > .votes");
			var numvotes = parseInt(votes.text(), 10);
			numvotes++;
			votes.text(numvotes);
		};
		if (action['action'] === 'vote_comment') {
			var commentid = action['commentid'];
			var userid = action['userid'];
			if (userid === client.userid) {
				disable_vote(commentid);
			}
			var votes = $('#' + commentid + "> .stats > .votes");
			var numvotes = parseInt(votes.text(), 10);
			numvotes++;
			votes.text(numvotes);
		};
		if (action['action'] === 'unvote_post') {
			var postid = action['postid'];
			var userid = action['userid'];
			if (userid === client.userid) {
				enable_vote(postid);
			}
			var votes = $('#' + postid + "> .stats > .votes");
			var numvotes = parseInt(votes.text(), 10);
			numvotes--;
			votes.text(numvotes);
		};
		if (action['action'] === 'unvote_comment') {
			var commentid = action['commentid'];
			var userid = action['userid'];
			if (userid === client.userid) {
				enable_vote(commentid);
			}
			var votes = $('#' + commentid + "> .stats > .votes");
			var numvotes = parseInt(votes.text(), 10);
			numvotes--;
			votes.text(numvotes);
		};		
		if (action['action'] === 'flag_post') {
			var postid = action['postid'];
			var userid = action['userid'];
			if (userid === client.userid) {
				disable_flag(postid);
			}
			var flags = $('#' + postid + "> .stats > .flags");
			var numflags = parseInt(flags.text(), 10);
			numflags++;
			flags.text(numflags);
		};
		if (action['action'] === 'flag_comment') {
			var commentid = action['commentid'];
			var userid = action['userid'];
			if (userid === client.userid) {
				disable_flag(commentid);
			}
			var flags = $('#' + commentid + "> .stats > .flags");
			var numflags = parseInt(flags.text(), 10);
			numflags++;
			flags.text(numflags);
		};		
		if (action['action'] === 'unflag_post') {
			var postid = action['postid'];
			var userid = action['userid'];
				if (userid === client.userid) {
				enable_flag(postid);
			}
			var flags = $('#' + postid + "> .stats > .flags");
			var numflags = parseInt(flags.text(), 10);
			numflags--;
			flags.text(numflags);
		};
		if (action['action'] === 'unflag_comment') {
			var commentid = action['commentid'];
			var userid = action['userid'];
			if (userid === client.userid) {
				enable_flag(commentid);
			}
			var flags = $('#' + commentid + "> .stats > .flags");
			var numflags = parseInt(flags.text(), 10);
			numflags--;
			flags.text(numflags);
		};		
	};
	
	
	client.post = function(message) {
		$.get("/post/" + client.eventid + "/" + message);
	};
	client.post_anon = function(message) {
		$.get("/anon_post/" + client.eventid + "/" + message);
	}
	
	client.comment = function(postid, message) {
		$.get("/comment/" + postid + "/" + message);
	};
	client.comment_anon = function(postid, message) {
		$.get("/anon_comment/" + postid + "/" + message);
	};
	
	client.vote_comment = function(commentid) {
		$.get("/vote/comment/" + commentid);
	};
	
	client.unvote_comment = function(commentid) {
		$.get("/unvote/comment/" + commentid);
	};
	
	client.flag_comment = function(commentid) {
		$.get("/flag/comment/" + commentid);
	};
	
	client.unflag_comment = function(commentid) {
		$.get("/unflag/comment/" + commentid);
	};
	
	client.vote_post = function(postid) {
		$.get("/vote/post/" + postid);
	};
	
	client.unvote_post = function(postid) {
		$.get("/unvote/post/" + postid);
	};
	
	client.flag_post = function(postid) {
		$.get("/flag/post/" + postid);
	};
	
	client.unflag_post = function(postid, callback) {
		$.get("/unflag/post/" + postid);
	};
	
	client.can_vote = function(objectid) {
		for (index in client.voted) {
			if (client.voted[index] === objectid) return false;
		}
		return true;
	}
	
	client.can_flag = function(objectid) {
		for (index in client.flagged) {
			if (client.flagged[index] == objectid) return false;
		}
		return true;
	}
	
	var enable_vote = function(objectid) {
			var vote = $('#' + objectid + "> .actions > .vote");
			var unvote = $('#' + objectid + "> .actions > .unvote");
			unvote.attr('style', 'display:none;');
			vote.removeAttr('style');
	};
	
	var disable_vote = function(objectid) {
			var vote = $('#' + objectid + "> .actions > .vote");
			var unvote = $('#' + objectid + "> .actions > .unvote");
			vote.attr('style', 'display:none;');
			unvote.removeAttr('style');
	};
	var enable_flag = function(objectid) {
			var flag = $('#' + objectid + "> .actions > .flag");
			var unflag = $('#' + objectid + "> .actions > .unflag");
			unflag.attr('style', 'display:none;');
			flag.removeAttr('style');
	};
	
	var disable_flag = function(objectid) {
			var flag = $('#' + objectid + "> .actions > .flag");
			var unflag = $('#' + objectid + "> .actions > .unflag");
			flag.attr('style', 'display:none;');
			unflag.removeAttr('style');
	};
	
	
	var add_post_tag = function(postid, message, flags, votes, author_data) {
		var posts = $('#posts');
		
		var post = document.createElement('div');
		post.setAttribute('id', postid);
		post.setAttribute('class', 'post ' + author_data['type']);
		
		var author = document.createElement('div');
		author.setAttribute('class', 'author');
		author.innerHTML = author_data['first_name'] + " " + author_data['last_name'];
		post.appendChild(author);
		
		var message_tag = document.createElement('div');
		message_tag.setAttribute('class', 'message');
		message_tag.innerHTML = message;
		post.appendChild(message_tag);
		
		var post_actions = make_post_actions(postid);
		post.appendChild(post_actions);
		
		var stats = make_stats(flags, votes);
		post.appendChild(stats);
		
		var comments = document.createElement('div');
		comments.setAttribute('class', 'comments');
		post.appendChild(comments);
		
		var submit_comment = document.createElement('div');
		submit_comment.setAttribute('class', 'make_comment');
		
		var comment_input = document.createElement('input');
		comment_input.setAttribute('id', 'comment_input_for_' + postid);
		comment_input.setAttribute('type', 'text');
		comment_input.setAttribute('value', 'Add your comment');
		
		var comment_share = document.createElement('input');
		comment_share.setAttribute('id', 'comment_share_for_' + postid);
		comment_share.setAttribute('type', 'button');
		comment_share.setAttribute('value', 'Contribute');
		
		var anon_comment_share = document.createElement('input');
		anon_comment_share.setAttribute('id', 'anon_comment_share_for_' + postid);
		anon_comment_share.setAttribute('type', 'button');
		anon_comment_share.setAttribute('value', 'Anonymous Contribute');
		
		submit_comment.appendChild(comment_input);
		submit_comment.appendChild(comment_share);
		submit_comment.appendChild(anon_comment_share);
		post.appendChild(submit_comment);
		
		
		posts.prepend(post);
		
		//Bind button actions
		$('#comment_input_for_' + postid).bind('focus', function() {
			$('#comment_input_for_' + postid).val("");
		});
		
		$('#comment_share_for_' + postid).bind('click', function() {
			var message = $('#comment_input_for_' + postid).val();
			if(!(message === "")) {
				console.log(message);
				client.comment(postid, message);
				$('#comment_input_for_' + postid).val("");
			}
		});
		
		$('#anon_comment_share_for_' + postid).bind('click', function() {
			var message = $('#comment_input_for_' + postid).val();
			if(!(message === "")) {
				console.log(message);
				client.comment_anon(postid, message);
				$('#comment_input_for_' + postid).val("");
			}
		});
	};

	var add_comment_tag = function(postid, commentid, message, flags, votes, author_data) {
		var comments = $('#' + postid + " .comments");
		
		var comment = document.createElement('div');
		comment.setAttribute('id', commentid);
		comment.setAttribute('class', 'comment ' + author_data['type']);
		
		var author = document.createElement('div');
		author.setAttribute('class', 'author');
		author.innerHTML = author_data['first_name'] + " " + author_data['last_name'];
		comment.appendChild(author);
		
		var message_tag = document.createElement('div');
		message_tag.setAttribute('class', 'message');
		message_tag.innerHTML = message;
		comment.appendChild(message_tag);
		
		var comment_actions = make_comment_actions(commentid);
		comment.appendChild(comment_actions);
		
		console.log("Making stats for " + message);
		console.log("flags " + flags);
		console.log("votes " + votes);
		var stats = make_stats(flags, votes);
		comment.appendChild(stats); 
		comments.append(comment);
	};
	
	//Todo: make_post/comment_actions => make_object_actions
	var make_post_actions = function(postid) {
		var canvote = client.can_vote(postid);
		var canflag = client.can_flag(postid);
		var post_actions = document.createElement('div');
		post_actions.setAttribute('class', 'actions');
		
		var vote = document.createElement('a');
		vote.setAttribute('href', 'javascript:;');
		vote.setAttribute('class', 'vote');
		vote.setAttribute('onclick', 'client.vote_post("' + postid + '");');
		vote.innerHTML = 'vote';
		
		var unvote = document.createElement('a');
		unvote.setAttribute('href', 'javascript:;');
		unvote.setAttribute('class', 'unvote');
		unvote.setAttribute('onclick', 'client.unvote_post("' + postid + '");');
		unvote.innerHTML = 'unvote';
		
		var flag = document.createElement('a');
		flag.setAttribute('href', 'javascript:;');
		flag.setAttribute('class', 'flag');
		flag.setAttribute('onclick', 'client.flag_post("' + postid + '");');
		flag.innerHTML = 'flag';
		
		var unflag = document.createElement('a');
		unflag.setAttribute('href', 'javascript:;');
		unflag.setAttribute('class', 'unflag');
		unflag.setAttribute('onclick', 'client.unflag_post("' + postid + '");');
		unflag.innerHTML = 'unflag';
		
		if(canvote) {
			unvote.setAttribute('style', 'display:none;');
		} else {
			vote.setAttribute('style', 'display:none;');
		}
		
		if(canflag) {
			unflag.setAttribute('style', 'display:none;');
		} else {
			flag.setAttribute('style', 'display:none;');
		}
		
		post_actions.appendChild(vote);
		post_actions.appendChild(unvote);
		post_actions.appendChild(flag);
		post_actions.appendChild(unflag);
		return post_actions;
	};
	
	var make_comment_actions = function(commentid) {
		var canvote = client.can_vote(commentid);
		var canflag = client.can_flag(commentid);
		var comment_actions = document.createElement('div');
		comment_actions.setAttribute('class', 'actions');
		
		var vote = document.createElement('a');
		vote.setAttribute('href', 'javascript:;');
		vote.setAttribute('class', 'vote');
		vote.setAttribute('onclick', 'client.vote_comment("' + commentid + '");');
		vote.innerHTML = 'vote';
		
		var unvote = document.createElement('a');
		unvote.setAttribute('href', 'javascript:;');
		unvote.setAttribute('class', 'unvote');
		unvote.setAttribute('onclick', 'client.unvote_comment("' + commentid + '");');
		unvote.innerHTML = 'unvote';
		
		var flag = document.createElement('a');
		flag.setAttribute('href', 'javascript:;');
		flag.setAttribute('class', 'flag');
		flag.setAttribute('onclick', 'client.flag_comment("' + commentid + '");');
		flag.innerHTML = 'flag';
		
		var unflag = document.createElement('a');
		unflag.setAttribute('href', 'javascript:;');
		unflag.setAttribute('class', 'unflag');
		unflag.setAttribute('onclick', 'client.unflag_comment("' + commentid + '");');
		unflag.innerHTML = 'unflag';
		
		if(canvote) {
			unvote.setAttribute('style', 'display:none;');
		} else {
			vote.setAttribute('style', 'display:none;');
		}
		
		if(canflag) {
			unflag.setAttribute('style', 'display:none;');
		} else {
			flag.setAttribute('style', 'display:none;');
		}
		
		comment_actions.appendChild(vote);
		comment_actions.appendChild(unvote);
		comment_actions.appendChild(flag);
		comment_actions.appendChild(unflag);
		return comment_actions;
	};

	var make_stats = function(flags, votes) {
		var stats = document.createElement('div');
		stats.setAttribute('class', 'stats');
		
		var votes_tag = document.createElement('div');
		votes_tag.setAttribute('class', 'votes');
		votes_tag.innerHTML = votes;
		
		var flags_tag = document.createElement('div');
		flags_tag.setAttribute('class', 'flags');
		flags_tag.innerHTML = flags;
		
		stats.appendChild(votes_tag);
		stats.appendChild(flags_tag);
		return stats;
	};
})();
