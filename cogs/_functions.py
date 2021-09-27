def split_add(list, discriminator=""):
    list = list.split()
    list_str = ""
    for element in list:
        list_str += element
        list_str += discriminator
    if list_str[len(list_str) - 1] == discriminator:
        list_str = list_str[0:len(list_str) - 1]
    return list_str
