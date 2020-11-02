function openAnswer(answer_id, url) {
    console.log("openAnswer....");
    var entry = $('[data-frequently-entry="' + answer_id + '"]');
    if (!entry.attr('data-frequently-opened')) {
        entry.attr('data-frequently-opened', 'true');
        $.post(
            url,
            {
                "csrfmiddlewaretoken": getCSRFToken(),
                "get_answer": answer_id
            },
            function(data) {
                $(data).insertAfter('[data-frequently-entry="' + answer_id + '"]');
                initializeForm();
            }
        );
    }
}

function hideAnswer(answer_id) {
    $('[data-answer-id="' + answer_id + '"]').remove();
    $('[data-frequently-entry="' + answer_id + '"]').removeAttr('data-frequently-opened');
}

function getCSRFToken() {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            if (cookie.substring(0, 10) == ('csrftoken' + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(10));
                break;
            }
        }
    }
    return cookieValue;
}

function initializeForm() {
    $('[data-class="frequently-form"] input[type="submit"]').click(function() {
        var form = $(this).closest('[data-class="frequently-form"]');
        var data = form.serializeArray();
        data.push({ name: this.name, value: this.value });
        form.find('input[type="submit"]').attr('disabled', true);
        $.post(form.attr('action'), data, function(data) {
            form.find('input[type="submit"]').remove();
            refreshRating(form.attr('id'), form.attr('action'));
            form.prepend(data).find('[data-class="send-feedback"]').click(function() {
                data = form.serializeArray();
                data.push({ name: this.name, value: this.value });
                $.post(form.attr('action'), data, function(data) {
                    form.find('[data-class="feedback-form"]').remove();
                    form.prepend(data);
                });
                return false;
            });
        });
        return false;
    });
}

function refreshRating(rating_id, url) {
    $.post(
        url,
        {
            "csrfmiddlewaretoken": getCSRFToken(),
            "rating_id": rating_id
        },
        function(data) {
            $('.' + rating_id).html(data);
        }
    );
}