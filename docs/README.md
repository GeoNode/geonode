#GeoNode Documentation

Welcome to the GeoNode Documentation.

#Translate The Documentation
1. Dump pot file into i18n folder

    $ sphinx-build -b gettext . i18n/pot
  
2. Translate pot file using Transifex or Poedit

3. Save .po and .mo files into
    
    $ i18n/$(LANG)/LC_MESSAGES
    
    Note: Transifex allows to download .po file. Once the translation is ready, select "Download for use" in order to get the .po translated version.
          Put the .po tranlsated file into 'i18n/$(LANG)/LC_MESSAGES' and rename it as the original .pot file maintaining the .po extension.
          Use the command 'sphinx-intl build' in order to generate the .mo compiled translation for Sphinx.
          
          The 'sphinx-intl' can be installed with 'pip install sphinx-intl'
    
    More: http://sphinx-doc.org/latest/intl.html
    
4. Build the doc

    # Windows
    $ make html en
    
    # Linux
    $ make html LANG=en

##License Information
Documentation
Documentation is released under a [Creative Commons] license with the following conditions.

You are free to Share (to copy, distribute and transmit) and to Remix (to adapt) the documentation under the following conditions:

Attribution. You must attribute the documentation to the author.
Share Alike. If you alter, transform, or build upon this work, you may distribute the resulting work only under the same or similar license to this one.
With the understanding that:

Any of the above conditions can be waived if you get permission from the copyright holder.
Public Domain. Where the work or any of its elements is in the public domain under applicable law, that status is in no way affected by the license.
Other Rights. In no way are any of the following rights affected by the license:

Your fair dealing or fair use rights, or other applicable copyright exceptions and limitations;
The author’s moral rights;
Rights other persons may have either in the work itself or in how the work is used, such as publicity or privacy rights.
Notice: For any reuse or distribution, you must make clear to others the license terms of this work. The best way to do this is with a link to this web page.

You may obtain a copy of the License at Creative Commons Attribution-ShareAlike 3.0 Unported License

The document is written in reStructuredText format for consistency and portability.

##Author Information
This documentation was written by GeoNode and GeoServer Communities.

The layout for the reStructuredText based documentation is based on the work done by the GeoNode project and the Sphinx framework.

#Creative Commons
Creative Commons Attribution-ShareAlike 3.0 Unported License Creative Commons (CC) is a non-profit organization devoted to expanding the range of creative works available for others to build upon legally and to share. The organization has released several copyright-licenses known as Creative Commons licenses free of charge to the public. These licenses allow creators to communicate which rights they reserve, and which rights they waive for the benefit of recipients or other creators. An easy-to-understand one-page explanation of rights, with associated visual symbols, explains the specifics of each Creative Commons license. Creative Commons licenses do not replace copyright, but are based upon it. They replace individual negotiations for specific rights between copyright owne (licensor) and licensee, which are necessary under an “all rights reserved” copyright management, with a “some rights reserved” management employing standardized licenses for re-use cases where no commercial compensation is sought by the copyright owner. The result is an agile, low-overhead and low-cost copyright-management regime, profiting both copyright owners and licensees.
