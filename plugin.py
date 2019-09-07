###############################################################################
#    Copyright (c) 2019 Salvatore Ventura <salvoventura@gmail.com>
#
#      File: plugin.py
#
#    Author: Salvatore Ventura <salvoventura@gmail.com>
#      Date: 9/5/2019
#   Purpose: Plugin for Sigil Ebook - https://sigil-ebook.com/
#            Create an Index of all Figures in the book
#
#  Revision: 1
#   Comment: What's new in revision 1
#
#   Limited option for the way images are tagged, which has to be exactly
#   with these tags:
#
#   <p><img alt="image010" src="../Images/image010.png"/><br/>
#   <span class="image_caption">Figure 8 - DSLR diagram</span></p>
#
#  NOTE: DO NOT INDENT plugin.xml!!! It will fail validation.
###############################################################################
import sys

DOC_V3 = '''\
<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
    <head>
        <title>
            {title}
        </title>
    </head>
    <body>
        <h1>{h1}</h1>
        {body}
    </body>
</html>'''

DOC_V2 = '''\
<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
    <head>
        <title>
            {title}
        </title>
    </head>
    <body>
        <h1>{h1}</h1>
        {body}
    </body>
</html>'''


def process_book(bk):
    '''
    Process each file in the book by:
    1. finding images that are supposed to be indexed (TBD)
    2. adding an anchor to them
    3. preparing a list that contains references to these anchors to return

    :param bk:
    :return: list of anchor+captions references
    '''

    # use built in quickparser
    parser = bk.qp
    # caption list for reference
    captions = []

    # For each file in the book
    for file_id, href in bk.text_iter():
        print('    processing {}...'.format(href))
        data = bk.readfile(file_id)  # load the file
        parser.setContent(data)  # parse the data

        full_document = []
        paragraph = []

        updated = False

        inside_p = False
        found_img = False
        found_br = False
        found_span = False
        img_name = None
        img_caption = None

        # loop through all tags modifying if needed and converting back to xhtml
        for text, tagprefix, tname, ttype, tattr, in parser.parse_iter():

            # The best way is to shelf every paragraph and modify only the ones that
            # meet all the conditions in the specific order. But need to complete the
            # paragraph before any flushing nevertheless.

            # We are looking for img that is followed by a caption in span
            # <p><img alt="image010" src="../Images/image010.png"/><br/>
            # <span class="image_caption">Figure 8 - DSLR diagram</span></p>

            # The way it's currently done doesn't guarantee the order, but just
            # the presence of various elements.

            # Another interesting way would be to use a control sequence
            # that tracks what tag was received and in which order.
            # Future development should also include a way to verify via class name.
            # I mean, it can get very complicated, very fast, and there isn't one right way.
            #

            if not inside_p:
                # we haven't started a paragraph yet
                if tname == 'p' and ttype in ['begin']:
                    # we found a starting paragraph
                    inside_p = True
                    paragraph = [parser.tag_info_to_xml(tname, ttype, tattr)]
                    continue

                # Haven't started a paragraph, hence we dump everything in the main doc
                if text is not None:
                    full_document.append(text)
                else:
                    full_document.append(parser.tag_info_to_xml(tname, ttype, tattr))
                continue

            if inside_p:
                # we are inside a paragraph: everything will be shelved
                paragraph.append(parser.tag_info_to_xml(tname, ttype, tattr))

                # test conditions
                if tname == 'p' and ttype in ['end']:
                    # This is a closing tag, we must dump.
                    # Let's first check if we found all we needed
                    if all([found_img, found_br, found_span]):
                        # We found everything: insert the anchor, save the (img, caption)
                        img_ref_id = 'ref_' + img_name
                        open_anchor = parser.tag_info_to_xml('a', 'begin', {'id': img_ref_id})
                        close_anchor = parser.tag_info_to_xml('a', 'end')
                        paragraph.insert(2, close_anchor)
                        paragraph.insert(1, open_anchor)
                        captions.append((img_ref_id, img_caption, href))
                        updated = True

                    # Just dump everything and reset
                    for _ in paragraph:
                        full_document.append(_)

                    # Reset
                    img_name, img_caption, paragraph = None, None, []
                    inside_p, found_img, found_br, found_span = False, False, False, False
                    continue

                if tname == 'img' and ttype in ['single']:
                    # we got an img: read the tags
                    found_img = True
                    img_name = tattr.get('alt', 'Noname')

                if tname == 'br' and ttype in ['single']:
                    # we got a br
                    found_br = True

                if tname == 'span':
                    if ttype in ['begin', 'single']:
                        # we got a span open
                        found_span = True

                if text is not None:
                    paragraph.append(text)
                    if all([found_img, found_br, found_span]):
                        img_caption = text

        # rebuild the xhtml text, and write to file, if anything got changed
        if updated:
            print('    updating file {}...'.format(href))
            data = "".join(full_document)
            bk.writefile(file_id, str(data))

    # print(captions)
    return captions


def make_index_of_figures_page(bk, captions):
    # Now prepare the Index of Figures page from the captions
    parser = bk.qp
    index = []
    for img_ref_id, img_caption, href in captions:
        index.append(
            parser.tag_info_to_xml('p', 'begin', {'class': 'iof_entry'}) +
            parser.tag_info_to_xml('a', 'begin', {'href': '../' + href + '#' + img_ref_id}) +
            img_caption.strip() +
            parser.tag_info_to_xml('a', 'end') +
            parser.tag_info_to_xml('p', 'end'))

    epubversion = "2.0"
    if bk.launcher_version() >= 20160102:
        epubversion = bk.epub_version()

    body = '\n'.join(index)
    if epubversion.startswith("3"):
        data = DOC_V3.format(**{'title': 'Index of figures', 'h1': 'Index of figures', 'body': body})
    else:
        data = DOC_V2.format(**{'title': 'Index of figures', 'h1': 'Index of figures', 'body': body})

    basename = "IndexOfFigures.xhtml"
    mimetype = "application/xhtml+xml"
    uid_iof = 'indexoffigures'
    bk.addfile(uid_iof, basename, data, mimetype)


def run(bk):
    # Process each file in the book
    print('Start processing book for images with captions...')
    captions = process_book(bk)
    # If we found some figures that needed captions, we'll also make the index file
    if captions:
        print('Preparing the index of figures file')
        make_index_of_figures_page(bk, captions)
    else:
        print('Nothing to do')
    return 0

#
# BACKUP
#
def run2(bk):
    # easiest to use built in quickparser for this
    parser = bk.qp
    updated = False

    # For each file in the book
    for file_id, href in bk.text_iter():
        data = bk.readfile(file_id)  # load the file
        parser.setContent(data)  # parse the data

        output = []
        shelf = []
        inside_p = False
        found_img = False
        found_br = False
        found_span = False
        img_name = None
        img_caption = None

        # caption list for reference
        captions = []

        # loop through all tags modifying if needed and converting back to xhtml
        for text, tagprefix, tname, ttype, tattr, in parser.parse_iter():

            # The best way is to shelf every paragraph and modify only the ones that
            # meet all the conditions in the specific order. But need to complete the
            # paragraph before any flushing nevertheless.

            # We are looking for img that is followed by a caption in span
            # <p><img alt="image010" src="../Images/image010.png"/><br/>
            # <span class="image_caption">Figure 8 - DSLR diagram</span></p>
            print(shelf)
            if tname == 'p':
                if ttype in ['begin'] and not inside_p:
                    # we got a p opening: hold it to check if the next is an image
                    inside_p = True
                    shelf = []
                    shelf.append(parser.tag_info_to_xml(tname, ttype, tattr))

                elif ttype in ['end'] and all([inside_p, found_img, found_br, found_span]):
                    shelf.append(parser.tag_info_to_xml(tname, ttype, tattr))
                    # modify, flush and reset
                    # '<p>',
                    # '<img alt="image010" src="../Images/image010.png"/>',
                    # '<br/>',
                    # '<span class="image_caption">',
                    # 'Figure 8 - DSLR diagram',
                    # '</span>',
                    # '</p>'
                    open_anchor = parser.tag_info_to_xml('a', 'begin', {'id': 'ref_' + img_name})
                    close_anchor = parser.tag_info_to_xml('a', 'end')
                    shelf.insert(2, close_anchor)
                    shelf.insert(1, open_anchor)
                    captions.append((img_name, img_caption))
                    img_name = None
                    img_caption = None
                    updated = True

                    for _ in shelf:
                        output.append(_)
                    shelf = []
                    inside_p = False
                    found_img = False
                    found_br = False
                    found_span = False
                else:
                    # flush
                    pass

                continue

            if tname == 'img' and ttype in ['single']:
                # we got an img after a p: shelf it, and read the tags
                if inside_p:
                    found_img = True
                    img_name = tattr.get('alt', 'Noname')
                    shelf.append(parser.tag_info_to_xml(tname, ttype, tattr))
                else:
                    # flush and reset
                    for _ in shelf:
                        output.append(_)
                    shelf = []
                    inside_p = False
                    found_img = False
                    found_br = False
                    found_span = False
                continue

            if tname == 'br' and ttype in ['single']:
                # we got a br after an img: shelf it
                if found_img:
                    found_br = True
                    shelf.append(parser.tag_info_to_xml(tname, ttype, tattr))
                else:
                    # flush and reset
                    for _ in shelf:
                        output.append(_)
                    shelf = []
                    inside_p = False
                    found_img = False
                    found_br = False
                    found_span = False
                continue

            if tname == 'span':
                if ttype in ['begin', 'single']:
                    # we got a span after a br: shelf it
                    if found_br:
                        found_span = True
                        shelf.append(parser.tag_info_to_xml(tname, ttype, tattr))
                    else:
                        # flush and reset
                        for _ in shelf:
                            output.append(_)
                        shelf = []
                        inside_p = False
                        found_img = False
                        found_br = False
                        found_span = False
                    continue

                elif ttype in ['end']:
                    if found_span:
                        shelf.append(parser.tag_info_to_xml(tname, ttype, tattr))
                    continue

            # Text is special, so we either push it onto the shelf or into the output buffer
            if text is not None:
                if found_span:
                    img_caption = text
                    shelf.append(img_caption)
                else:
                    output.append(text)
                continue

            # push the tag into the output buffer
            # we should reach this point only if all the conditions above fail
            output.append(parser.tag_info_to_xml(tname, ttype, tattr))

        # rebuild the xhtml text, and write to file, if anything got changed
        if updated:
            data = "".join(output)
            bk.writefile(file_id, str(data))
    return 0


def main():
    print("I reached main when I should not have")
    return -1


if __name__ == "__main__":
    sys.exit(main())
