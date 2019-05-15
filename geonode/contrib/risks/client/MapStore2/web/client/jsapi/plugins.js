/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

module.exports = {
    plugins: {
        MousePositionPlugin: require('../plugins/MousePosition'),
        PrintPlugin: require('../plugins/Print'),
        IdentifyPlugin: require('../plugins/Identify'),
        TOCPlugin: require('../plugins/TOC'),
        BackgroundSwitcherPlugin: require('../plugins/BackgroundSwitcher'),
        MeasurePlugin: require('../plugins/Measure'),
        MeasureResultsPlugin: require('../plugins/MeasureResults'),
        MapPlugin: require('../plugins/Map'),
        ToolbarPlugin: require('../plugins/Toolbar'),
        DrawerMenuPlugin: require('../plugins/DrawerMenu'),
        ShapeFilePlugin: require('../plugins/ShapeFile'),
        SnapshotPlugin: require('../plugins/Snapshot'),
        SettingsPlugin: require('../plugins/Settings'),
        ExpanderPlugin: require('../plugins/Expander'),
        SearchPlugin: require('../plugins/Search'),
        ScaleBoxPlugin: require('../plugins/ScaleBox'),
        LocatePlugin: require('../plugins/Locate'),
        ZoomInPlugin: require('../plugins/ZoomIn'),
        ZoomOutPlugin: require('../plugins/ZoomOut'),
        ZoomAllPlugin: require('../plugins/ZoomAll'),
        MapLoadingPlugin: require('../plugins/MapLoading'),
        HelpPlugin: require('../plugins/Help'),
        HomePlugin: require('../plugins/Home'),
        MetadataExplorerPlugin: require('../plugins/MetadataExplorer'),
        LoginPlugin: require('../plugins/Login'),
        OmniBarPlugin: require('../plugins/OmniBar'),
        BurgerMenuPlugin: require('../plugins/BurgerMenu'),
        UndoPlugin: require('../plugins/History'),
        RedoPlugin: require('../plugins/History'),
        MapsPlugin: require('../plugins/Maps'),
        MapSearchPlugin: require('../plugins/MapSearch'),
        LanguagePlugin: require('../plugins/Language'),
        ManagerPlugin: require('../plugins/manager/Manager'),
        RulesManagerPlugin: require('../plugins/manager/RulesManager'),
        ManagerMenuPlugin: require('../plugins/manager/ManagerMenu'),
        SharePlugin: require('../plugins/Share'),
        SavePlugin: require('../plugins/Save'),
        SaveAsPlugin: require('../plugins/SaveAs')
    },
    requires: {
        ReactSwipe: require('react-swipeable-views').default,
        SwipeHeader: require('../components/data/identify/SwipeHeader')
    }
};
