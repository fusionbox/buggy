jQuery(function($) {
  $('select[name="projects"]').select2();
  $('select[name="project"]').select2();

  $('.actions .subActions').hide();
  $('.nestedAction .open').click(function() {
    $('.actions > button, .actions .open').hide();
    $(this).closest('.nestedAction').find('.subActions').show();
    return false;
  });

  $('.subActions .cancel').click(function() {
    $(this).closest('.nestedAction').find('.subActions').hide();
    $('.actions > button, .actions .open').show();
    return false;
  });

  $('textarea[name="comment"]').atwho({
    at: '@',
    data: window.buggy_user_names,
  }).atwho({
    at: '#',
    data: window.buggy_open_bugs,
    displayTpl: '<li data-value="#${number}">#${number} <small>${title}</small></li>',
    insertTpl: '#${number}',
    searchKey: 'number',
    callbacks: {
      // We don't want to match at the beginning of the line, because that will
      // be a markdown header instead of a bug mention.
      matcher: function(flag, subtext) {
        var regexp = /^.*\S.*[ \t\f\v]#(\d*)$/gim;
        var match = regexp.exec(subtext);
        if (match)
          return match[1];
        else
          return null;
      }
    }
  });
});
