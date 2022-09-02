// Javascript functions for the revealer as a whole

var Revealer = {
  
  createBoundLabeledSlider: function(sliderElement, inputElement, labelContainer, labels, sliderOpts){
    var self = this;
    sliderElement = $(sliderElement);
    var handles = sliderElement.down('.handle');
    inputElement = $(inputElement);
    sliderOpts = sliderOpts || { };

    sliderOpts.onSlide = sliderOpts.onSlide || function(val) { 
      inputElement.value = val; 
    };
    
    sliderOpts.range = sliderOpts.range || $R(0, 100);
    
    var iv = inputElement ? inputElement.value : 0;
    
    sliderOpts.sliderValue = sliderOpts.sliderValue || iv;
    var slider = new Control.Slider(handles, sliderElement, sliderOpts);
    slider.handles.invoke('removeClassName', 'selected');
    self.buildLabels(slider, labelContainer, labels);
    return slider;
  },
  
  buildLabels : function(slider, labelContainer, labels) {
        
    var self = this;
    
    labelContainer = $(labelContainer);
    labels = labels || [];
    
    var handleWidth = slider.handles[0].offsetWidth;
    var width = slider.trackLength - (handleWidth);
    labelContainer.style.width = self.labelContainerWidth(width, labels.length)+"px";
    var lw = self.labelWidth(width, labels.length);
    labelContainer.style.marginLeft = self.containerMargin(lw, handleWidth)+"px";
    labels.each(function(message) {
      labelContainer.insert(self.buildLabel(lw, message));
    });
  },
  
  labelContainerWidth: function(sliderWidth, labelCount) {
    return (2*labelCount*sliderWidth)/((2*labelCount) - 2);
  },
  
  labelWidth: function(sliderWidth, labelCount) {
    return (2*sliderWidth)/((2*labelCount) - 2);
  },
  
  containerMargin: function(labelWidth, handleWidth) {
    // I'm not sure why I need to use handleWidth / 3. Is it just a value
    // that happens to work for this 17px wide handle?
    // It does not, thankfully, depend on the label count.
    return -((labelWidth/2) - (handleWidth/3));
  },
  
  buildLabel: function(width, message) {
    if (!message || message == '') {
      message = '&nbsp;'
    }
    var label = new Element('label', {'style': 'width:'+width+'px'}).update(
      new Element('div').update(message)
    );
    return label;
  },
  
  Delayed : Behavior.create({
    initialize: function(delay_ms) {
      if (delay_ms === undefined) {
        delay_ms = 500;
      }
      delay_ms = delay_ms + 0; // coerce to numeric type
      var elem = $(this.element);
      elem.disabled = "true";
      elem.addClassName("delayed");
      window.setTimeout(function() {
          elem.disabled = "";
          elem.removeClassName("delayed");
        }, 
        delay_ms
      );
    }
  }),
  
  // A form that disallows multiple submissions. I know, js is the wrong
  // place to do this. Whatevs.
  SingleSubmit : Behavior.create({
    initialize: function() {
    },
    
    onsubmit: function(evt) {
      var submitters = this.element.select("input[type=submit], button");
      for (var i = 0; i < submitters.length; i++) {
        submitters[i].onclick = function(button_evt) {
          button_evt.stop();
        }
      }
    },
  })
  
}

Revealer.Timeline = Class.create({
  initialize: function(eventList) {
    this.eventList = eventList;
    
  }
});

Revealer.Actions = {
  reveal : function(elements, newclass) {
    newclass = newclass || 'shown';
    elements.each(function(e) {
      e.addClassName(newclass);
    });
  }
};