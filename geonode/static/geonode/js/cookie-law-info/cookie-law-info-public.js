CLI_ACCEPT_COOKIE_NAME =(typeof CLI_ACCEPT_COOKIE_NAME !== 'undefined' ? CLI_ACCEPT_COOKIE_NAME : 'viewed_cookie_policy');
CLI_ACCEPT_COOKIE_EXPIRE =(typeof CLI_ACCEPT_COOKIE_EXPIRE !== 'undefined' ? CLI_ACCEPT_COOKIE_EXPIRE : 365);
CLI_COOKIEBAR_AS_POPUP=(typeof CLI_COOKIEBAR_AS_POPUP !== 'undefined' ? CLI_COOKIEBAR_AS_POPUP : false);
var CLI_Cookie={
	set: function (name, value, days) {
        if (days) {
            var date = new Date();
            date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
            var expires = "; expires=" + date.toGMTString();
        } else
            var expires = "";
        document.cookie = name + "=" + value + expires + "; path=/";
        if(days<1)
        {
            host_name=window.location.hostname;
            document.cookie = name + "=" + value + expires + "; path=/; domain=."+host_name+";";
            if(host_name.indexOf("www")!=1)
			{
			   var host_name_withoutwww=host_name.replace('www','');
			   document.cookie = name + "=" + value + expires + "; path=/; domain="+host_name_withoutwww+";";
			}
            host_name=host_name.substring(host_name.lastIndexOf(".", host_name.lastIndexOf(".")-1));
            document.cookie = name + "=" + value + expires + "; path=/; domain="+host_name+";";
        }
    },
    read: function (name) {
        var nameEQ = name + "=";
        var ca = document.cookie.split(';');
        for (var i = 0; i < ca.length; i++) {
            var c = ca[i];
            while (c.charAt(0) == ' ') {
                c = c.substring(1, c.length);
            }
            if (c.indexOf(nameEQ) === 0) {
                return c.substring(nameEQ.length, c.length);
            }
        }
        return null;
    },
    erase: function (name) {
        this.set(name, "", -10);
    },
    exists: function (name) {
        return (this.read(name) !== null);
    },
    getallcookies:function()
    {
	    var pairs = document.cookie.split(";");
	    var cookieslist = {};
	    for (var i = 0; i < pairs.length; i++) {
	        var pair = pairs[i].split("=");
	        cookieslist[(pair[0] + '').trim()] = unescape(pair[1]);
	    }
	    return cookieslist;
	}
}
var CLI=
{
	bar_config:{},
	showagain_config:{},
	set:function(args)
	{
		if(typeof JSON.parse !== "function")
		{
	        console.log("CookieLawInfo requires JSON.parse but your browser doesn't support it");
	        return;
	    }
	    this.settings = JSON.parse(args.settings);
	    this.bar_elm=jQuery(this.settings.notify_div_id);
	    this.showagain_elm = jQuery(this.settings.showagain_div_id);

        /* buttons */
        this.main_button=jQuery('.cli-plugin-main-button');
        this.main_link = jQuery('.cli-plugin-main-link');
        this.reject_link = jQuery('.cookie_action_close_header_reject');
        this.delete_link=jQuery(".cookielawinfo-cookie-delete");

        if(this.settings.cookie_bar_as=='popup')
    	{
    		CLI_COOKIEBAR_AS_POPUP=true;
    	}
        this.configBar();
        this.toggleBar();
        this.attachDelete();
        this.attachEvents();
        this.configButtons();
        var cli_hidebar_on_readmore=this.hideBarInReadMoreLink();
        if(this.settings.scroll_close===true && cli_hidebar_on_readmore===false)
        {
        	window.addEventListener("scroll",CLI.closeOnScroll, false);
    	}
	},
	hideBarInReadMoreLink:function()
	{
		if(CLI.settings.button_2_hidebar===true && this.main_link.length>0 && this.main_link.hasClass('cli-minimize-bar'))
		{
			this.hideHeader();
			this.showagain_elm.slideDown(this.settings.animate_speed_show);
			return true;
		}
		return false;
	},
	attachEvents:function()
	{
		jQuery('.cli_action_button').click(function(e){
			e.preventDefault();
			var elm=jQuery(this);
			var button_action=elm.attr('data-cli_action');
			var open_link=elm[0].hasAttribute("href") && elm.attr("href") != '#' ? true : false;
			var new_window=false;
			if(button_action=='accept')
			{
				CLI.accept_close();
				new_window=CLI.settings.button_1_new_win ? true : false;
			}else if(button_action=='reject')
			{
				CLI.reject_close();
				new_window=CLI.settings.button_3_new_win ? true : false;
			}
			if(open_link)
			{
                if(new_window)
                {
                    window.open(elm.attr("href"),'_blank');
                }else
                {
                    window.location.href =elm.attr("href");
                }
            }
		});
	},
	attachDelete:function()
	{
		this.delete_link.click(function () {
	        CLI_Cookie.erase(CLI_ACCEPT_COOKIE_NAME);
	        for(var k in Cli_Data.nn_cookie_ids)
	        {
	            CLI_Cookie.erase(Cli_Data.nn_cookie_ids[k]);
	        }
	        return false;
	    });
	},
	configButtons:function()
	{
	    /*[cookie_button] */
	    this.main_button.css('color',this.settings.button_1_link_colour);
	    if(this.settings.button_1_as_button)
	    {
	        this.main_button.css('background-color',this.settings.button_1_button_colour);
	        this.main_button.hover(function () {
	            jQuery(this).css('background-color',CLI.settings.button_1_button_hover);
	        },function (){
	            jQuery(this).css('background-color',CLI.settings.button_1_button_colour);
	        });
	    }

	    /* [cookie_link] */
	    this.main_link.css('color',this.settings.button_2_link_colour);
	    if(this.settings.button_2_as_button)
	    {
	        this.main_link.css('background-color',this.settings.button_2_button_colour);
	        this.main_link.hover(function () {
	            jQuery(this).css('background-color',CLI.settings.button_2_button_hover);
	        },function (){
                jQuery(this).css('background-color',CLI.settings.button_2_button_colour);
            });
	    }


	    /* [cookie_reject] */
	    this.reject_link.css('color',this.settings.button_3_link_colour);
	    if(this.settings.button_3_as_button)
	    {
	        this.reject_link.css('background-color',this.settings.button_3_button_colour);
	        this.reject_link.hover(function () {
	            jQuery(this).css('background-color',CLI.settings.button_3_button_hover);
	        },function () {
	            jQuery(this).css('background-color',CLI.settings.button_3_button_colour);
	        });
	    }
	},
	toggleBar:function()
	{
		if(CLI_COOKIEBAR_AS_POPUP)
		{
			this.barAsPopUp(1);
		}
		if(CLI.settings.cookie_bar_as=='widget')
		{
			this.barAsWidget(1);
		}
		if(!CLI_Cookie.exists(CLI_ACCEPT_COOKIE_NAME))
		{
	        this.displayHeader();
	    }else
	    {
	        this.hideHeader();
	    }
	    if(this.settings.show_once_yn)
	    {
	        setTimeout(function(){
	        	CLI.close_header();
	        },CLI.settings.show_once);
	    }

	    this.showagain_elm.click(function (e) {
	        e.preventDefault();
	        CLI.showagain_elm.slideUp(CLI.settings.animate_speed_hide,function()
	        {
	            CLI.bar_elm.slideDown(CLI.settings.animate_speed_show);
	            if(CLI_COOKIEBAR_AS_POPUP)
				{
					CLI.showPopupOverlay();
				}
	        });
	    });
	},
	configShowAgain:function()
	{
		this.showagain_config = {
	        'background-color': this.settings.background,
	        'color':this.l1hs(this.settings.text),
	        'position': 'fixed',
	        'font-family': this.settings.font_family
	    };
	    if(this.settings.border_on)
	    {
	        var border_to_hide = 'border-' + this.settings.notify_position_vertical;
	        this.showagain_config['border'] = '1px solid ' + this.l1hs(this.settings.border);
	        this.showagain_config[border_to_hide] = 'none';
	    }
	    var cli_win=jQuery(window);
    	var cli_winw=cli_win.width();
    	var showagain_x_pos=this.settings.showagain_x_position;
    	if(cli_winw<300)
    	{
    		showagain_x_pos=10;
    		this.showagain_config.width=cli_winw-20;
    	}else
    	{
    		this.showagain_config.width='auto';
    	}
	    var cli_defw=cli_winw>400 ? 500 : cli_winw-20;
	    if(CLI_COOKIEBAR_AS_POPUP) /* cookie bar as popup */
	    {
	    	var sa_pos=this.settings.popup_showagain_position;
	    	var sa_pos_arr=sa_pos.split('-');
	    	if(sa_pos_arr[1]=='left')
	    	{
	    		this.showagain_config.left=showagain_x_pos;
	    	}else if(sa_pos_arr[1]=='right')
	    	{
	    		this.showagain_config.right=showagain_x_pos;
	    	}
	    	if(sa_pos_arr[0]=='top')
	    	{
	    		this.showagain_config.top=0;

	    	}else if(sa_pos_arr[0]=='bottom')
	    	{
	    		this.showagain_config.bottom=0;
	    	}
	    	this.bar_config['position'] = 'fixed';

	    }else if(this.settings.cookie_bar_as=='widget')
	    {
	    	this.showagain_config.bottom=0;
	    	if(this.settings.widget_position=='left')
	    	{
	    		this.showagain_config.left=showagain_x_pos;
	    	}else if(this.settings.widget_position=='right')
	    	{
	    		this.showagain_config.right=showagain_x_pos;
	    	}
	    }
	    else
	    {
	    	if(this.settings.notify_position_vertical == "top")
		    {
		        this.showagain_config.top = '0';
		    }
		    else if(this.settings.notify_position_vertical == "bottom")
		    {
		        this.bar_config['position'] = 'fixed';
		        this.bar_config['bottom'] = '0';
		        this.showagain_config.bottom = '0';
		    }
		    if(this.settings.notify_position_horizontal == "left")
		    {
		        this.showagain_config.left =showagain_x_pos;
		    }else if(this.settings.notify_position_horizontal == "right")
		    {
		        this.showagain_config.right =showagain_x_pos;
		    }
	    }
	    this.showagain_elm.css(this.showagain_config);
	},
	configBar:function()
	{
		this.bar_config = {
	        'background-color':this.settings.background,
	        'color':this.settings.text,
	        'font-family':this.settings.font_family
	    };
	    if(this.settings.notify_position_vertical=="top")
	    {
	        this.bar_config['top'] = '0';
	        if(this.settings.header_fix === true)
	        {
	            this.bar_config['position'] = 'fixed';
	        }
	    }else
	    {
	        this.bar_config['bottom'] = '0';
	    }
	    this.configShowAgain();
	    this.bar_elm.css(this.bar_config).hide();
	},
	l1hs:function(str)
	{
	    if (str.charAt(0) == "#") {
	        str = str.substring(1, str.length);
	    } else {
	        return "#" + str;
	    }
	    return this.l1hs(str);
	},
	close_header:function()
	{
        CLI_Cookie.set(CLI_ACCEPT_COOKIE_NAME,'yes',CLI_ACCEPT_COOKIE_EXPIRE);
        this.hideHeader();
    },
	accept_close:function()
    {
        this.hidePopupOverlay();
        CLI_Cookie.set(CLI_ACCEPT_COOKIE_NAME,'yes',CLI_ACCEPT_COOKIE_EXPIRE);
        if(this.settings.notify_animate_hide)
        {
            this.bar_elm.slideUp(this.settings.animate_speed_hide);
        }else
        {
            this.bar_elm.hide();
        }
        if(this.settings.showagain_tab)
        {
        	this.showagain_elm.slideDown(this.settings.animate_speed_show);
        }
        if(this.settings.accept_close_reload === true)
        {
            this.reload_current_page();
        }
        return false;
    },
	reject_close:function()
    {
        this.hidePopupOverlay();
        for(var k in Cli_Data.nn_cookie_ids)
        {
            CLI_Cookie.erase(Cli_Data.nn_cookie_ids[k]);
        }
        CLI_Cookie.set(CLI_ACCEPT_COOKIE_NAME,'no',CLI_ACCEPT_COOKIE_EXPIRE);
        if(this.settings.notify_animate_hide)
        {
            this.bar_elm.slideUp(this.settings.animate_speed_hide);
        } else
        {
            this.bar_elm.hide();
        }
        if(this.settings.showagain_tab)
        {
        	this.showagain_elm.slideDown(this.settings.animate_speed_show);
        }
        if(this.settings.reject_close_reload === true)
        {
            this.reload_current_page();
        }
        return false;
    },
    reload_current_page:function()
    {
    	if(typeof cli_flush_cache!=='undefined' && cli_flush_cache==1)
    	{
            window.location.href=this.add_clear_cache_url_query();
    	}else
    	{
    		window.location.reload(true);
    	}
    },
    add_clear_cache_url_query:function()
    {
    	var cli_rand=new Date().getTime()/1000;
    	var cli_url=window.location.href;
    	var cli_hash_arr=cli_url.split('#');
    	var cli_urlparts= cli_hash_arr[0].split('?');
    	if(cli_urlparts.length>=2)
    	{
    		var cli_url_arr=cli_urlparts[1].split('&');
    		cli_url_temp_arr=new Array();
    		for(var cli_i=0; cli_i<cli_url_arr.length; cli_i++)
    		{
    			var cli_temp_url_arr=cli_url_arr[cli_i].split('=');
    			if(cli_temp_url_arr[0]=='cli_action')
    			{

    			}else
    			{
    				cli_url_temp_arr.push(cli_url_arr[cli_i]);
    			}
    		}
    		cli_urlparts[1]=cli_url_temp_arr.join('&');
    		cli_url=cli_urlparts.join('?')+(cli_url_temp_arr.length>0 ? '&': '')+'cli_action=';
    	}else
    	{
    		cli_url=cli_hash_arr[0]+'?cli_action=';
    	}
    	cli_url+=cli_rand;
    	if(cli_hash_arr.length>1)
    	{
    		cli_url+='#'+cli_hash_arr[1];
    	}
    	return cli_url;
    },
	closeOnScroll:function()
	{
        if(window.pageYOffset > 100 && !CLI_Cookie.read(CLI_ACCEPT_COOKIE_NAME))
        {
            CLI.accept_close();
            if(CLI.settings.scroll_close_reload === true)
            {
                window.location.reload();
            }
            window.removeEventListener("scroll",CLI.closeOnScroll,false);
        }
    },
    displayHeader:function()
    {
        if(this.settings.notify_animate_show)
        {
            this.bar_elm.slideDown(this.settings.animate_speed_show);
        }else
        {
            this.bar_elm.show();
        }
        this.showagain_elm.hide();
        if(CLI_COOKIEBAR_AS_POPUP)
		{
			this.showPopupOverlay();
		}
    },
    hideHeader:function()
    {
        if(this.settings.showagain_tab)
        {
	        if(this.settings.notify_animate_show)
	        {
	            this.showagain_elm.slideDown(this.settings.animate_speed_show);
	        } else {
	            this.showagain_elm.show();
	        }
    	}else
    	{
    		this.showagain_elm.hide();
    	}
        this.bar_elm.slideUp(this.settings.animate_speed_show);
        this.hidePopupOverlay();
    },
    hidePopupOverlay:function()
    {
        jQuery('body').removeClass("cli-barmodal-open");
        jQuery(".cli-popupbar-overlay").removeClass("cli-show");
    },
    showPopupOverlay:function()
    {
        if(this.settings.popup_overlay)
        {
        	jQuery('body').addClass("cli-barmodal-open");
        	jQuery(".cli-popupbar-overlay").addClass("cli-show");
    	}
    },
    barAsWidget:function(a)
    {
    	var cli_elm=this.bar_elm;
	    var cli_win=jQuery(window);
	    var cli_winh=cli_win.height()-40;
	    var cli_winw=cli_win.width();
	    var cli_defw=cli_winw>400 ? 300 : cli_winw-30;
	    cli_elm.css({
	        'width':cli_defw,'height':'auto','max-height':cli_winh,'padding':'25px 15px','overflow':'auto','position':'fixed','box-sizing':'border-box'
	    });
	    if(this.settings.widget_position=='left')
	    {
	    	cli_elm.css({
	        	'left':'15px','right':'auto','bottom':'15px','top':'auto'
	    	});
	    }else
	    {
	    	cli_elm.css({
	        	'left':'auto','right':'15px','bottom':'15px','top':'auto'
	    	});
	    }
	    if(a)
	    {
	    	this.setResize();
		}
    },
    barAsPopUp:function(a)
    {
    	if(typeof cookie_law_info_bar_as_popup==='function')
    	{
    		return false;
    	}
    	var cli_elm=this.bar_elm;
	    var cli_win=jQuery(window);
	    var cli_winh=cli_win.height()-40;
	    var cli_winw=cli_win.width();
	    var cli_defw=cli_winw>700 ? 500 : cli_winw-20;

	    cli_elm.css({
	        'width':cli_defw,'height':'auto','max-height':cli_winh,'bottom':'','top':'50%','left':'50%','margin-left':(cli_defw/2)*-1,'margin-top':'-100px','padding':'25px 15px','overflow':'auto'
	    }).addClass('cli-bar-popup cli-modal-content');


	    cli_h=cli_elm.height();
	    li_h=cli_h<200 ? 200 : cli_h;
	    cli_elm.css({'top':'50%','margin-top':((cli_h/2)+30)*-1});
	    setTimeout(function(){
		    cli_elm.css({
		        'bottom':''
		    });
	     },100);
	    if(a)
	    {
	    	this.setResize();
		}
    },
    setResize:function()
	{
		var resizeTmr=null;
		jQuery(window).resize(function() {
			clearTimeout(resizeTmr);
			resizeTmr=setTimeout(function()
			{
				if(CLI_COOKIEBAR_AS_POPUP)
				{
					CLI.barAsPopUp();
				}
				if(CLI.settings.cookie_bar_as=='widget')
				{
					CLI.barAsWidget();
				}
				CLI.configShowAgain();
			},500);
		});
	}
}
jQuery(document).ready(function() {
    if(typeof cli_cookiebar_settings!='undefined')
    {
	    CLI.set({
	      settings:cli_cookiebar_settings
	    });
	}
});
