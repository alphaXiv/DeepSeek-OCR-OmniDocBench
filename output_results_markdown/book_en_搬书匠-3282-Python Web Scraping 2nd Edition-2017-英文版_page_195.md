The structure of the search results can be examined with your browser tools, as shown here:

![Screenshot of a browser (Google Chrome) displaying a Google search results page for 'test'. The browser's Developer Tools panel is open, showing the HTML structure of the search results. The results are structured as links (<a>) whose parent element is an <h3> tag with class 'r'.]()This image shows a Google search results page for the query 'test'. The browser's Developer Tools are open, highlighting the HTML structure of a search result link. The link element (`<a>`) is shown to be nested within an `<h3>` tag that has the class attribute set to 'r' (`<h3 class="r">`).

![](_page_0_Picture_2.jpeg)

Here, we see that the search results are structured as links whose parent element is a <h3> tag with class "r".

To scrape the search results, we will use a CSS selector, which was introduced in Chapter 2,  
*Scraping the Data*:

```
>>> from lxml.html import fromstring
>>> import requests
>>> html = requests.get('https://www.google.com/search?q=test')
>>> tree = fromstring(html.content)
>>> results = tree.cssselect('h3.r a')
>>> results
[<Element a at 0x7f3d9affeaf8>,
 <Element a at 0x7f3d9affe890>,
 <Element a at 0x7f3d9affe8e8>,
 <Element a at 0x7f3d9affeaa0>,
 <Element a at 0x7f3d9b1a9e68>,
 <Element a at 0x7f3d9b1a9c58>,
 <Element a at 0x7f3d9b1a9ec0>,
 <Element a at 0x7f3d9b1a9f18>,
 <Element a at 0x7f3d9b1a9f70>,
 <Element a at 0x7f3d9b1a9fc8>]
```