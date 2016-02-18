$(document).ready(function () {
  var canvas, bbcanvas, context, bbcontext, tool, tracePoints,
      offseth, offsetw, canvas_img, current_slide, slide_name;

  function init () {
    // Find the canvas element.
    canvas = $('#traces_canvas');
    bbcanvas = $('#blackboard_canvas');
    var cparent = canvas.parent();
    
    if (!canvas) {
      alert('Error: I cannot find the canvas element!');
      return;
    }

    if (!canvas[0].getContext) {
      alert('Error: no canvas.getContext!');
      return;
    }

    // Get the 2D canvas context.
    context = canvas[0].getContext('2d');
    bbcontext = bbcanvas[0].getContext('2d');
    context.canvas.width  = cparent.width();
    context.canvas.height = cparent.height();
    bbcontext.canvas.width  = cparent.width();
    bbcontext.canvas.height = cparent.height();
    
    offl = cparent.offset().left;
    offt = cparent.offset().top;
    if (!context) {
      alert('Error: failed to getContext!');
      return;
    }

    // Pencil tool instance.
    tool = new tool_pencil();

    // Attach the mousedown, mousemove and mouseup event listeners.
    canvas.bind('mousedown', ev_canvas);
    canvas.bind('mousemove', ev_canvas);
    canvas.bind('mouseup',   ev_canvas);
    
    $('#NextButton').bind('click', next_slide);
    $('#PrevButton').bind('click', prev_slide);
    $('#ClearButton').bind('click', clearTraces);
    canvas_img=new Image();
    canvas_img.onload = function(){
      bbcontext.drawImage(canvas_img, 0, 0, bbcontext.canvas.width, bbcontext.canvas.height);
    };
    canvas_img.onerror = function(){
      bbcontext.drawImage(canvas_img, 0, 0, bbcontext.canvas.width, bbcontext.canvas.height);
    };
    current_slide = 0;
    slide_name = "pp.pdf";
  }

  function clearTraces() {
    context.clearRect(0, 0, bbcontext.canvas.width, bbcontext.canvas.height);
  }
  
  function next_slide() {
    current_slide += 1;
    canvas_img.src="slide?slideNumber=" + current_slide + "&slideName=" + slide_name;
  }
  
  function prev_slide() {
    if (current_slide > 0)
      current_slide -= 1;      
    canvas_img.src="slide?slideNumber=" + current_slide + "&slideName=" + slide_name;
  }
  
  // This painting tool works like a drawing pencil which tracks the mouse 
  // movements.
  function tool_pencil () {
    var tool = this;
    this.started = false;
    var lastTrace = new Array();
    // This is called when you start holding down the mouse button.
    // This starts the pencil drawing.
    this.mousedown = function (ev) {
      context.beginPath();
      context.lineWidth = 3;
      context.strokeStyle = "#0000ff";
      context.moveTo(ev.clientX-offl, ev.clientY-offt);
      lastTrace.push([ev.clientX-offl, ev.clientY-offt]);
      tool.started = true;
      tracePoints = [];
      tracePoints.push([ev.clientX-offl, ev.clientY-offt]);
    };

    // This function is called every time you move the mouse. Obviously, it only 
    // draws if the tool.started state is set to true (when you are holding down 
    // the mouse button).
    this.mousemove = function (ev) {
      if (tool.started) {
        context.lineTo(ev.clientX-offl, ev.clientY-offt);
        lastTrace.push([ev.clientX-offl, ev.clientY-offt]);
        tracePoints.push([ev.clientX-offl, ev.clientY-offt]);
        context.stroke();
      }
    };

    // This is called when you release the mouse button.
    this.mouseup = function (ev) {
      if (tool.started) {
        tool.mousemove(ev);
        tool.started = false;
        data = [];
        data = "points="+JSON.stringify(tracePoints);
        $.ajax({url: "/a/blackboard/new", type: "POST", dataType: "text",
                data: data, success: function(){},
                error: function(){}});        
      }
    };
  }

  // The general-purpose event handler. This function just determines the mouse 
  // position relative to the canvas element.
  function ev_canvas (ev) {
    if (ev.layerX || ev.layerX == 0) { // Firefox
      ev._x = ev.layerX;
      ev._y = ev.layerY;
    } else if (ev.offsetX || ev.offsetX == 0) { // Opera
      ev._x = ev.offsetX;
      ev._y = ev.offsetY;
    }

    // Call the event handler of the tool.
    var func = tool[ev.type];
    if (func) {
      func(ev);
    }
  }

  var bbupdater = {
    errorSleepTime: 500,
    cursor: null,

    poll: function() {
      var args = {"_xsrf": getCookie("_xsrf")};
      //if (updater.cursor) args.cursor =  updater.cursor;
      $.ajax({url: "/a/blackboard/updates", type: "POST", dataType: "text",
              data: $.param(args), success: bbupdater.onSuccess,
              error: bbupdater.onError});
    },

    onSuccess: function(response) {
      try {
        bbupdater.newMessages(eval("(" + response + ")"));
      } catch (e) {
        bbupdater.onError();
        return;
      }
      bbupdater.errorSleepTime = 500;

      window.setTimeout(bbupdater.poll, 0);
    },

    onError: function(response) {
      bbupdater.errorSleepTime *= 2;
      console.log("Poll error; sleeping for", bbupdater.errorSleepTime, "ms");
      window.setTimeout(bbupdater.poll, bbupdater.errorSleepTime);
    },

    newMessages: function(response) {
      if (!response.messages) return;
      //updater.cursor = response.cursor;
      var messages = response.messages;
      //updater.cursor = messages[messages.length - 1].id;
      //console.log(messages.length, "new messages, cursor:", updater.cursor);
      for (var i = 0; i < messages.length; i++) {
        bbupdater.showMessage(messages[i]);
      }
    },

    showMessage: function(message) {
      canvas = $('#traces_canvas');
      if (!canvas) {
        alert('Error: I cannot find the canvas element!');
        return;
      }
      if (!canvas[0].getContext) {
        alert('Error: no canvas.getContext!');
        return;
      }
      context = canvas[0].getContext('2d');        
      context.beginPath();
      context.lineWidth = 3;
      context.strokeStyle = "#0000ff";
      points = JSON.parse(message['points']);
      p0 = points[0];
      context.moveTo(p0[0], p0[1]);
      for (i = 1; i < points.length; i++)
      {
        pi = points[i];
        context.lineTo(pi[0], pi[1]);
      }
      context.stroke();
    }
  };
  
  init();
  bbupdater.poll();
});


