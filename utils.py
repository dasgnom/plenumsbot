def join_url(fragments, trailing_slash=False):
    """
    Joins the strings from the fragments list, with slashes, avoiding
    double or tripple slashes, if an element of fragments starts and / or 
    ends with a slash. Leading and trailing slashes will be preserved.
    A trailing slash can be added by setting trailing_slash to True.
    
    Args:
        fragments (list): parts to be joined with slashes
        trailing_slash (bool, optional): Add a trailing slash if True. Defaults to False.
    
    Returns:
        str: The elements from fragments, joined with single slashes

    Raises:
        TypeError
    """
    if not isinstance(fragments, list):
        raise TypeError("Fragments is not a list.")

    for idx in range(0, len(fragments)):
        if not isinstance(fragments[idx], str):
            raise TypeError("All parts of fragments have to be of type string.")
        if idx == 0:
            fragments[idx] = fragments[idx].rstrip("/")
        elif idx == len(fragments) - 1:
            fragments[idx] = fragments[idx].lstrip("/")
        else:
            fragments[idx].strip("/")
    joined = "/".join(fragments)
    if trailing_slash and not joined[:-1] == "/":
        joined += "/"
    return joined
