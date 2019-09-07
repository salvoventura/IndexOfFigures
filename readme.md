Index of Figures - A Sigil Plugin
=================================
**Index of Figures** is a plugin for [Sigil Ebook - https://sigil-ebook.com/](https://sigil-ebook.com/) 
with the purpose of generating an Index page with references to all the
images in the eBook document.

Images are automatically assigned an anchor id, which is then referenced
in the generated index page.


Installation
------------
This plugin has been tested working with Sigil version **0.9.18**.
You will need the IndexOfFigures_vX.Y.Z.zip file.

For installation instructions, please refer to the official Sigil 
documentation. The 0.9.18 documentation eBook is available [at this url](https://github.com/Sigil-Ebook/Sigil/blob/master/docs/Sigil_User_Guide_2019.09.03.epub?raw=true) .


Requirements
------------
At the moment, there are few requirements for the plugin to work:

- *img* tag must have the *alt* attribute set to a unique value 
- image caption must be inside a *span* section following the *img*
- *img* and *span* must be separated by a single *br*
- the whole thing in enclosed in a paragraph *p*

In other words, for an image to be picked up by the plugin, it must look
like the following:

    <p><img alt="image010" src="../Images/image010.png"/><br/>
    <span class="image_caption">Figure 8 - DSLR diagram</span></p>


Version
-------
**Index of Figures** v0.1.0 (alpha, v1)

License
-------
**Index of Figures** is released under the [MIT License](http://www.opensource.org/licenses/MIT) .