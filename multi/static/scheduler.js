var Reveal = Reveal || { };

Reveal.scheduler = function(sched_name, log_to_elt) {
  // Private methods
  var my = {};
  my.sched_list = [];
  my.sched_name = sched_name || '';
  my.log_to_elt = $(log_to_elt);
  my.logger = Reveal.logger(sched_name, [], log_to_elt);
  
  var pub = {};
  
  pub.run = function() {
    my.logger.add("Run started");
    for (var i=0, li = my.sched_list.length; i < li; i++) {
      var task = my.sched_list[i];
      // We need to bind the current value of task to window.setTimeout;
      // do this by creating and immediately calling an anomymous function.
      var f = function(t) {
        window.setTimeout(
          function() {
            // Provide a logger object to the caller
            var l = my.logger.sublogger(t.label)
            l.add("Task started");
            t.fx(l);
          },
          t.time);
      }(task);
      my.logger.add("Scheduled "+task.label);
    }
  };
  
  pub.add = function(tl, label, fx) {
    var t = tl;
    if (!tl.hasOwnProperty('label')) {
      t = Reveal.task(tl, label, fx);
    }
    if (t.label === '') {
      t.label = "task_"+(my.sched_list.length+1);
    }
    my.sched_list.push(t);
  };
  
  // slice() to return a copy of the array
  pub.get_tasks = function() { return my.sched_list.slice(); };
  pub.get_log = function() {
    return my.logger.get_event_list();
  }
  
  return pub;
};

// Just a shorthand object for storing tasks.
Reveal.task = function(time, label, fx) {
  return {'time': time, 'label':label, 'fx': fx};
};

Reveal.logger = function(tag, event_list, bind_element) {
  var my = {};
  my.tag = tag || '';
  my.event_list = event_list || [];
  my.bound_element = $(bind_element);
  
  // Publicly-accessible members and functions.
  var pub = {};
  
  // Add a log message, automatically tagging and timestamping it.
  pub.add = function(message) {
    le = {
      'time' : new Date().getTime(),
      'tag' : my.tag,
      'message' : message
    };
    my.event_list.push(le);
    if (my.bound_element && my.bound_element.value !== undefined ) {
      my.bound_element.value = my.event_list.toJSON();
    }
    return le;
  };
  
  // slice() to return a copy of the array.
  pub.get_event_list = function() {
    return my.event_list.slice();
  }
  
  pub.sublogger = function(tag) {
    return Reveal.logger(my.tag+"."+tag, my.event_list, my.bound_element);
  }
  
  return pub;
};

Reveal.log_event = function(time, tag, message) {
  var my = {};
  my.time = time;
  my.tag = tag;
  my.message = message;
  
  var pub = {};
  
}