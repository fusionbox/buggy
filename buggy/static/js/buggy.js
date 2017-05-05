jQuery(function($) {
  var buggyData = {};

  function parseBuggyData() {
    ["previewMarkdownUrl", "openBugs", "userNames", "bugActions", "harvestPlatformConfig"].map(function(key) {
      buggyData[key] = JSON.parse($("#buggyData-" + key).text() || null);
    });
    window._harvestPlatformConfig = buggyData.harvestPlatformConfig;
  }
  parseBuggyData();

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
    data: buggyData.userNames,
  }).atwho({
    at: '#',
    data: buggyData.openBugs,
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

    $.post(buggyData.previewMarkdownUrl, {preview: markdown}, function(resp) {
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
  var pjaxRequestPending = false;
  var pjaxRequestCanceled = false;

  $(document).on('pjax:beforeSend', function() {
    pjaxRequestPending = true;
    pjaxRequestCanceled = false;
    $('#pjax-container').addClass('loading');
  });

  $(document).on('pjax:complete', function() {
    pjaxRequestPending = false;
    $('#add-preset-url').val(location.pathname + location.search);

    if (pjaxRequestCanceled) {
      pjaxRequestCanceled = false;
      pjaxSubmit();
    } else {
      pjaxRequestCanceled = false;
    }

    $('#pjax-container').removeClass('loading');
  });

  $(document).on('pjax:end', function() {
    setActiveBulkActions();
    parseBuggyData();
    $('.subActions').hide();
    $('.actions > button, .actions .open').show();
  });

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
  });

  $(document).on('submit', 'form[data-pjax]', function(event) {
    $.pjax.submit(event, '#pjax-container');
  });
  $('form[data-pjax] :input:not(#id_search)').on('change', pjaxSubmit);
  $('form[data-pjax] #id_search').on('keyup paste', pjaxSubmit);

  $(document).on('pjax:popstate', location.reload);

  // Bulk Actions
  function intersection(arrays) {
    if (arrays.length > 0) {
      return arrays.reduce(function(previous, current){
        return previous.filter(function(element){
          return current.indexOf(element) > -1;
        });
      });
    } else {
      return [];
    }
  }

  function bugCountDescription(n) {
    if (n === 0) {
      return 'No bugs selected';
    } else if (n === 1) {
      return '1 bug selected';
    } else {
      return n + ' bugs selected';
    }
  }

  function setActiveBulkActions() {
    var bugNumbers = $('input[name=bugs]:checked').closest('tr').map(function(i, x) {
      return $(x).data('number');
    }).get();
    $('.offCanvasForm').toggleClass('active', bugNumbers.length > 0);
    $('#selected-count').text(bugCountDescription(bugNumbers.length));
    $('#check_all_bugs').prop(
      'checked', $('input[name=bugs]:checked').length === $('input[name=bugs]').length
    );
    var actionLists = bugNumbers.map(function(x) { return buggyData.bugActions[x]; });
    var allowedActions = intersection(actionLists);
    $('.offCanvasForm button[name=action]').each(function(i, e) {
      $(e).prop('disabled', allowedActions.indexOf(e.value) < 0);
    });
    $('.offCanvasForm .nestedAction > button').each(function(i, e) {
      var hasActiveChildren = $(e).siblings('.subActions').find('button[name=action]:enabled').length > 0;
      $(e).prop('disabled', !hasActiveChildren);
    });
  }

  $(document).on('change', '#check_all_bugs', function() {
    $('input[name=bugs]').prop('checked', $(this).prop('checked'));
  });
  $(document).on('change', 'input[name=bugs], #check_all_bugs', setActiveBulkActions);

  $(document).on('change', 'input[name=bugs]', function() {
    $(this).closest('tr').toggleClass('checked', $(this).prop('checked'));
  });

  setActiveBulkActions();

  // prevent double submissions
  $('form').on('submit', function() {
    $(this).on('click', 'button[type="submit"]', function() {
      return false;
    });
  });
});

jQuery.pjax.defaults.scrollTo = false;
jQuery.pjax.defaults.timeout = 2500;
