/**
 * Object SideNavi
 * public methods : init
 * init param : String direction
 * init param : Object css data
 */

var SideNavi = ( function () {

	var container = {},
		cssElements = {},
		posStep = 30,
		posStart = null,
		posEnd = null,
		posDirection = '',
		isSlideing = false,
		isVisible = false,
		activeIndex = -1,
		changeVisibility = false;

	function getPosStart () {

		if (posStart === null) {

			switch (posDirection) {
				case 'right' :
					posStart = $(cssElements.item + ':eq(0)', container).height()*1;
					break;
				case 'left' :
					posStart = 0 - $(cssElements.data + ':eq(0)', container).width()*1;
					break;
			}
		}

		return posStart;
	}
	function getPosEnd () {

		if (posEnd === null) {

			switch (posDirection) {
				case 'right' :
					posEnd = getPosStart();
					posEnd += $(cssElements.data, container).width()*1;
					break;
				case 'left' :
					posEnd = 0;
					break;
			}
		}

		return posEnd;
	}
	function getPos (){
		return container.css(posDirection).replace('px','');
	}
	function toggleIsVisible () {
		isVisible = !(isVisible);
	}
	function isActiveItem (item) {
		return item.hasClass('active');
	}
	function setActiveTab () {
		$(cssElements.tab + cssElements.active, container).removeClass(cssElements.active.replace('.',''));
		$(cssElements.tab + ':eq(' + activeIndex + ')',container).addClass(cssElements.active.replace('.',''));
	}
	function removeActiveItem () {
		$(cssElements.item + cssElements.active, container).removeClass('active');
	}
	function setActiveItem (item) {
		removeActiveItem();
		setActiveTab();
		item.addClass('active');
	}
	function slideEvent () {

		var pos = getPos()*1;

		if ( isVisible && pos < getPosEnd () || ! isVisible && pos > getPosStart ()  ) {

			pos = (isVisible) ?  pos+posStep : pos-posStep;

			if (isVisible && pos + posStep >= getPosEnd () || ! isVisible && pos - posStep <= getPosStart ()) {

				pos = (isVisible) ?  getPosEnd () : getPosStart ();
				container.css(posDirection, pos+'px');
				isSlideing = false;

			} else {
				container.css(posDirection, pos+'px');
				setTimeout(function () {slideEvent()}, 30 );
			}

		} else {
			isSlideing = false;
		}

	}
	function slide () {
		if ( ! isSlideing) {
			isSlideing = true;
			slideEvent();
		}
	}
	function setEventParam (item) {

		activeIndex = $(cssElements.item, container).index(item);

		if (isActiveItem(item)) {

			toggleIsVisible();
			removeActiveItem();
			changeVisibility = true;

		} else {

			setActiveItem(item);

			if ( ! isVisible) {
				toggleIsVisible();
				changeVisibility = true;
			}
		}
	}
	function eventListener () {

		$(cssElements.item, container).on('click', function (event) {

			event.preventDefault();
			setEventParam($(this));

			if (changeVisibility) {
				slide();
			}
		});
	}
	function init (direction, conf) {

		posDirection = direction;
		cssElements = conf;
		container = $(cssElements.container);

		eventListener();
	}

	return {
		init : init
	};

})();
