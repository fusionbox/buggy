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

  // Pjax
  $.pjax.defaults.scrollTo = false;
  var pjaxRequestPending = false;
  var pjaxRequestCanceled = false;

  $(document).on('pjax:send', function() {
    pjaxRequestPending = true;
    pjaxRequestCanceled = false;
    $('#pjax-container').addClass('loading');
  })

  $(document).on('pjax:complete', function() {
    pjaxRequestPending = false;
    $('#add-preset-url').val(location.pathname + location.search)

    if (pjaxRequestCanceled) {
      pjaxRequestCanceled = false;
      pjaxSubmit();
    } else {
      pjaxRequestCanceled = false;
    }

    $('#pjax-container').removeClass('loading');
  })

  function pjaxSubmit() {
    if (pjaxRequestPending) {
      pjaxRequestCanceled = true;
      return;
    } else {
      $('form[data-pjax]').submit();
    }
  }

  $(document).on('click', 'a[data-pjax]', function(event) {
    $.pjax.click(event, '#pjax-container');
  })

  $(document).on('submit', 'form[data-pjax]', function(event) {
    $.pjax.submit(event, '#pjax-container');
  });
  $('form[data-pjax] :input:not(#id_search)').on('change', pjaxSubmit);
  $('form[data-pjax] #id_search').on('keyup', pjaxSubmit);

  $(document).on('pjax:popstate', function(event) {
    location.reload();
  });
});
