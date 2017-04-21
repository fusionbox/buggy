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
    data: window.buggyData.userNames,
  }).atwho({
    at: '#',
    data: window.buggyData.openBugs,
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


  // Only allow one request to preview markdown to the server at a time, but
  // always do a preview with the latest content too.
  var requestPending = false;
  var requestCancelled = false;

  function doPreview($container) {
    if (requestPending) {
      requestCancelled = true;
      return;
    }
    requestPending = true;

    var markdown = $container.find('[name="comment"]').val();

    $.post(window.buggyData.previewMarkdownUrl, {preview: markdown}, function(resp) {
      $container.find('.previewTarget').html(resp).show();
      requestPending = false;
      if (requestCancelled) {
        requestCancelled = false;
        doPreview($container);
      }
    });
  }

  $('.previewMarkdown').click(function() {
    var $container = $(this).closest('.commentMarkdown');

    $container.find('[name="comment"]').on('keyup', function() {
      doPreview($container);
    });
    doPreview($container);

    return false;
  });
});
