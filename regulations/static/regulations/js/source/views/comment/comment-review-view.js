'use strict';

var $ = require('jquery');
var URI = require('urijs');
var _ = require('underscore');
var Backbone = require('backbone');
Backbone.$ = $;

var MainEvents = require('../../events/main-events');
var CommentEvents = require('../../events/comment-events');
var comments = require('../../collections/comment-collection');

function selfOrChild($root, selector) {
  return $root.is(selector) ? $root : $root.find(selector);
}

function toggleInput($container, enabled) {
  $container.toggle(enabled);
  selfOrChild($container, 'input, select').prop('disabled', !enabled);
}

var CommentReviewView = Backbone.View.extend({
  events: {
    'click .edit-comment': 'editComment',
    'click .preview-button': 'preview',
    'change .agree': 'toggleSubmit'
  },

  initialize: function(options) {
    Backbone.View.prototype.setElement.call(this, '#' + options.id);

    this.$content = this.$el.find('.comment-review-items');

    this.docId = this.$el.data('doc-id');
    this.template = _.template($('#comment-template').html());

    this.previewLoading = false;

    this.render();
  },

  findElms: function() {
    this.$form = this.$el.find('form');
    this.$submit = this.$el.find('.submit-button');
    this.$agree = this.$el.find('.agree');
  },

  editComment: function(e) {
    var section = $(e.target).closest('li').data('section');
    var options = {id: section, section: section, mode: 'write'};

    $('#content-body').removeClass('comment-review-wrapper');

    MainEvents.trigger('section:open', section, options, 'preamble-section');
    CommentEvents.trigger('comment:writeTabOpen');
  },

  render: function() {
    var commentData = comments.toJSON({docId: this.docId});
    var html = this.template({
      comments: commentData,
      previewLoading: this.previewLoading
    });

    this.$content.html(html);
    this.findElms();

    this.toggleSubmit();

    this.initTabs();
    this.initDependencies();

    this.$form.find('[name="comments"]').val(JSON.stringify(commentData));

    CommentEvents.trigger('comment:writeTabOpen');
  },

  initTabs: function() {
    var self = this;
    function updateTabs(tab, tabSet) {
      var tabSelector = '[data-tab="' + tab + '"]';
      var setSelector = '[data-tab-set="' + tabSet + '"]';
      self.$el.find(setSelector).removeClass('current');
      self.$el.find(setSelector + tabSelector).addClass('current');
      self.$el.find(setSelector + '[data-tabs]').each(function(idx, elm) {
        var $elm = $(elm);
        var tabs = $elm.data('tabs');
        if (tabs.indexOf(tab) !== -1) {
          $elm.show();
        } else {
          $elm.hide();
        }
      });
    }
    var $tabs = self.$el.find('[data-tab]');
    updateTabs($tabs.data('tab'), $tabs.data('tab-set'));
    $tabs.on('click', function() {
      var $tab = $(this);
      updateTabs($tab.data('tab'), $tab.data('tab-set'));
    });
  },

  /**
   * The regs.gov field definitions include compound fields in the sense that
   * one select filters the options of another. When the first select leads to
   * _no_ options available in the second, we need to display a "write-in".
   **/
  initDependencies: function() {
    var self = this;
    self.$el.find('[data-depends-on]').each(function(idx, elm) {
      var $elm = $(elm);
      var $select = selfOrChild($elm, 'select');
      var $dependsOn = self.$el.find('[name="' + $elm.data('depends-on') + '"]');
      var $options = $select.find('option[value]').detach().clone();
      var $writeIn = self.$el.find('[data-writein-for="' + $select.prop('id') + '"]');
      function updateOptions(value) {
        $select.find('option[value]').remove();
        var $valid = $options.filter(function(idx, elm) {
          return $(elm).data('dependency') === value;
        }).get();
        toggleInput($writeIn, $valid.length === 0);
        toggleInput($elm, $valid.length > 0);
        $select.append($valid);
        $select.val(null);
      }
      updateOptions($dependsOn.val());
      $dependsOn.on('change', function() {
        updateOptions($(this).val());
      });
    });
  },

  preview: function() {
    var $xhr = $.ajax({
      type: 'POST',
      url: window.APP_PREFIX + 'comments/preview',
      data: JSON.stringify({
        assembled_comment: comments.toJSON({docId: this.docId})
      }),
      contentType: 'application/json',
      dataType: 'json'
    });
    $xhr.then(this.previewSuccess.bind(this));
    this.previewLoading = true;
    this.render();
  },

  previewSuccess: function(resp) {
    window.location = resp.url;
    this.previewLoading = false;
    this.render();
  },

  toggleSubmit: function() {
    if (this.$agree.length) {
      this.$submit.prop('disabled', !this.$agree.prop('checked'));
    }
  }
});

module.exports = CommentReviewView;
