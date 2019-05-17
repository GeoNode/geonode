/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require('react');

const I18N = require('../../../components/I18N/I18N');
const {Panel, Button, Carousel, CarouselItem} = require('react-bootstrap');

const carouselImages = {
    viewer: require('../../assets/img/Viewer.png'),
    "3dviewer": require('../../assets/img/3DViewer.png'),
    mouseposition: require('../../assets/img/MousePosition.png'),
    scalebar: require('../../assets/img/ScaleBar.png'),
    layertree: require('../../assets/img/LayerTree.png'),
    queryform: require('../../assets/img/QueryForm.png'),
    featuregrid: require('../../assets/img/FeatureGrid.png'),
    print: require('../../assets/img/Print.png'),
    plugins: require('../../assets/img/Plugins.png'),
    api: require('../../assets/img/Api.png'),
    rasterstyler: require('../../assets/img/rasterstyler.png')
};

var Examples = React.createClass({
    render() {
        return (<Panel id="mapstore-examples-applications" className="mapstore-home-examples">
            <h3><I18N.Message msgId="home.Applications"/></h3>
            <Carousel>
                <CarouselItem>
                  <img width={900} height={500} alt="900x500" src={carouselImages.viewer}/>
                  <div className="carousel-caption">
                    <I18N.HTML msgId="home.examples.viewer.html" />
                    <Button href="#/viewer/leaflet/0" bsStyle="info" bsSize="large" target="_blank"><I18N.Message msgId="home.open" /></Button>
                  </div>
                </CarouselItem>
                <CarouselItem>
                  <img width={900} height={500} alt="900x500" src={carouselImages['3dviewer']}/>
                  <div className="carousel-caption">
                      <I18N.HTML msgId="home.examples.3dviewer.html" />
                    <Button href="examples/3dviewer" bsStyle="info" bsSize="large" target="_blank"><I18N.Message msgId="home.open" /></Button>
                  </div>
                </CarouselItem>
                <CarouselItem>
                  <img width={900} height={500} alt="900x500" src={carouselImages.mouseposition}/>
                  <div className="carousel-caption">
                      <I18N.HTML msgId="home.examples.mouseposition.html" />
                    <Button href="examples/mouseposition" bsStyle="info" bsSize="large" target="_blank"><I18N.Message msgId="home.open" /></Button>
                  </div>
                </CarouselItem>
                <CarouselItem>
                  <img width={900} height={500} alt="900x500" src={carouselImages.scalebar}/>
                  <div className="carousel-caption">
                      <I18N.HTML msgId="home.examples.scalebar.html" />
                    <Button href="examples/scalebar" bsStyle="info" bsSize="large" target="_blank"><I18N.Message msgId="home.open" /></Button>
                  </div>
                </CarouselItem>
                <CarouselItem>
                  <img width={900} height={500} alt="900x500" src={carouselImages.layertree}/>
                  <div className="carousel-caption">
                      <I18N.HTML msgId="home.examples.layertree.html" />
                    <Button href="examples/layertree" bsStyle="info" bsSize="large" target="_blank"><I18N.Message msgId="home.open" /></Button>
                  </div>
                </CarouselItem>
                <CarouselItem>
                  <img width={900} height={500} alt="900x500" src={carouselImages.queryform}/>
                  <div className="carousel-caption">
                      <I18N.HTML msgId="home.examples.queryform.html" />
                    <Button href="examples/queryform" bsStyle="info" bsSize="large" target="_blank"><I18N.Message msgId="home.open" /></Button>
                  </div>
                </CarouselItem>
                <CarouselItem>
                  <img width={900} height={500} alt="900x500" src={carouselImages.featuregrid}/>
                  <div className="carousel-caption">
                      <I18N.HTML msgId="home.examples.featuregrid.html" />
                    <Button href="examples/featuregrid" bsStyle="info" bsSize="large" target="_blank"><I18N.Message msgId="home.open" /></Button>
                  </div>
                </CarouselItem>
                <CarouselItem>
                  <img width={900} height={500} alt="900x500" src={carouselImages.print}/>
                  <div className="carousel-caption">
                      <I18N.HTML msgId="home.examples.print.html" />
                    <Button href="examples/print" bsStyle="info" bsSize="large" target="_blank"><I18N.Message msgId="home.open" /></Button>
                  </div>
                </CarouselItem>
                <CarouselItem>
                  <img width={900} height={500} alt="900x500" src={carouselImages.plugins}/>
                  <div className="carousel-caption">
                      <I18N.HTML msgId="home.examples.plugins.html" />
                    <Button href="examples/plugins" bsStyle="info" bsSize="large" target="_blank"><I18N.Message msgId="home.open" /></Button>
                  </div>
                </CarouselItem>
                <CarouselItem>
                  <img width={900} height={500} alt="900x500" src={carouselImages.api}/>
                  <div className="carousel-caption">
                      <I18N.HTML msgId="home.examples.api.html" />
                    <Button href="examples/api" bsStyle="info" bsSize="large" target="_blank"><I18N.Message msgId="home.open" /></Button>
                  </div>
                </CarouselItem>
                <CarouselItem>
                  <img width={900} height={500} alt="900x500" src={carouselImages.rasterstyler}/>
                  <div className="carousel-caption">
                      <I18N.HTML msgId="home.examples.rasterstyler.html" />
                    <Button href="examples/rasterstyler" bsStyle="info" bsSize="large" target="_blank"><I18N.Message msgId="home.open" /></Button>
                  </div>
                </CarouselItem>
            </Carousel>
        </Panel>);
    }
});

module.exports = Examples;
