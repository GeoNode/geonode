/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');

const {
  ShareButtons,
  ShareCounts,
  generateShareIcon
} = require('react-share');

// components of the socialnetworks grouped in a bigger container aka ShareSocials
const {
  FacebookShareButton,
  GooglePlusShareButton,
  LinkedinShareButton,
  TwitterShareButton
} = ShareButtons;

// counter for counting the number of map-sharing on a given social network
const {
  FacebookShareCount,
  GooglePlusShareCount,
  LinkedinShareCount
} = ShareCounts;

// icons of the social network
const FacebookIcon = generateShareIcon('facebook');
const TwitterIcon = generateShareIcon('twitter');
const GooglePlusIcon = generateShareIcon('google');
const LinkedinIcon = generateShareIcon('linkedin');
const Message = require('../../components/I18N/Message');
require('./share.css');

const ShareSocials = React.createClass({
    propTypes: {
        shareUrl: React.PropTypes.string,
         getCount: React.PropTypes.func,
         shareTitle: React.PropTypes.string
    },
    getDefaultProps() {
        return {
            shareTitle: 'GeoSolutions'
        };
    },
  render() {
      let countProps = {};
      if (this.props.getCount) {
          countProps.getCount = this.props.getCount;
      }
      const title = this.props.shareTitle;

      return (
        <div className="social-links">

            <h4>
                <Message msgId="share.socialIntro"/>
            </h4>

            <div className="social-box facebook">
              <FacebookShareButton
                url={this.props.shareUrl}
                title={title}
                className="share-facebook">
                <FacebookIcon
                  size={32}
                  round />
              </FacebookShareButton>
              <FacebookShareCount
                url={this.props.shareUrl}
                {...countProps}
                className="share-facebook-count">
                {count => count}
              </FacebookShareCount>
            </div>

              <div className="social-box twitter">
                <TwitterShareButton
                  url={this.props.shareUrl}
                  title={title}
                  className="share-twitter">
                  <TwitterIcon
                    size={32}
                    round />
                </TwitterShareButton>
                <div className="share-twitter-count">
                  &nbsp;
                </div>
              </div>


              <div className="social-box google">
                <GooglePlusShareButton
                  url={this.props.shareUrl}
                  className="share-google-count">
                  <GooglePlusIcon
                    size={32}
                    round />
                </GooglePlusShareButton>
                <GooglePlusShareCount
                  url={this.props.shareUrl}
                  {...countProps}
                  className="share-google-count">
                  {count => count}
                </GooglePlusShareCount>
              </div>

              <div className="social-box linkedin">
                <LinkedinShareButton
                  url={this.props.shareUrl}
                  title={title}
                  className="share-linkedin-count">
                  <LinkedinIcon
                    size={32}
                    round />
                </LinkedinShareButton>
                  <LinkedinShareCount
                  url={this.props.shareUrl}
                  {...countProps}
                  className="share-linkedin-count">
                  {count => count}
                </LinkedinShareCount>
              </div>
      </div>
    );
  }
});

module.exports = ShareSocials;
