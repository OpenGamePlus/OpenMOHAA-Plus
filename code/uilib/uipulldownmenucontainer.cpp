/*
===========================================================================
Copyright (C) 2015 the OpenMoHAA team

This file is part of OpenMoHAA source code.

OpenMoHAA source code is free software; you can redistribute it
and/or modify it under the terms of the GNU General Public License as
published by the Free Software Foundation; either version 2 of the License,
or (at your option) any later version.

OpenMoHAA source code is distributed in the hope that it will be
useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with OpenMoHAA source code; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
===========================================================================
*/

#include "ui_local.h"

Event EV_UIPulldownMenuContainer_AddPopup
(
    "addpopup",
    EV_DEFAULT,
    "ssss",
    "menuname title type string",
    "Adds a popup to the list box.\n"
    "menuname - the name of the menu to add this to\n"
    "title - the string to display\n"
    "type - type of item this is (command,cvar,event_name)\n"
    "string - the data that corresponds to the correct type\n"
);

Event EV_UIPulldownMenuContainer_MenuShader
(
    "menushader",
    EV_DEFAULT,
    "ss",
    "menuname shader",
    "Adds a menu to the container and sets the shader.\n"
    "menuname - the name of the menu to add this to\n"
    "shader - the string to display"
);

Event EV_UIPulldownMenuContainer_SelectedMenuShader
(
    "selmenushader",
    EV_DEFAULT,
    "ss",
    "menuname shader",
    "Adds a menu to the container and sets the shader when it's selected.\n"
    "menuname - the name of the menu to add this to\n"
    "shader - the string to display"
);

Event EV_UIPulldownMenuContainer_PopupHighlightFGColor
(
    "popup_highlight_fgcolor",
    EV_DEFAULT,
    "sffff",
    "menu r g b a",
    "Set the highlight background color of the popup menu\n"
    "menu - the name of the popup menu to color\n"
);

Event EV_UIPulldownMenuContainer_HighlightBGColor
(
    "highlight_bgcolor",
    EV_DEFAULT,
    "sffff",
    "menu r g b a",
    "Set the highlight foreground color of the pulldown menu\n"
    "menu - the name of the popup menu to color\n"
);

Event EV_UIPulldownMenuContainer_HighlightFGColor
(
    "highlight_fgcolor",
    EV_DEFAULT,
    "sffff",
    "menu r g b a",
    "Set the highlight background color of the pulldown menu\n"
    "menu - the name of the popup menu to color\n"
);

Event EV_UIPulldownMenuContainer_PopupHighlightBGColor
(
    "popup_highlight_bgcolor",
    EV_DEFAULT,
    "sffff",
    "menu r g b a",
    "Set the highlight foreground color of the popup menu\n"
    "menu - the name of the popup menu to color\n"
);

Event EV_UIPulldownMenuContainer_PopupFGColor
(
    "popup_fgcolor",
    EV_DEFAULT,
    "sffff",
    "menu r g b a",
    "Set the background color of the popup menu\n"
    "menu - the name of the popup menu to color\n"
);

Event EV_UIPulldownMenuContainer_PopupBGColor
(
    "popup_bgcolor",
    EV_DEFAULT,
    "sffff",
    "menu r g b a",
    "Set the foreground color of the popup menu\n"
    "menu - the name of the popup menu to color\n"
);

CLASS_DECLARATION(UIWidget, UIPulldownMenuContainer, NULL) {
    {&EV_UIPulldownMenuContainer_AddPopup,              &UIPulldownMenuContainer::AddPopup                },
    {&EV_UIPulldownMenuContainer_MenuShader,            &UIPulldownMenuContainer::SetMenuShader           },
    {&EV_UIPulldownMenuContainer_SelectedMenuShader,    &UIPulldownMenuContainer::SetSelectedMenuShader   },
    {&EV_UIPulldownMenuContainer_PopupHighlightFGColor, &UIPulldownMenuContainer::SetPopupHighlightFGColor},
    {&EV_UIPulldownMenuContainer_PopupHighlightBGColor, &UIPulldownMenuContainer::SetPopupHighlightBGColor},
    {&EV_UIPulldownMenuContainer_PopupFGColor,          &UIPulldownMenuContainer::SetPopupFGColor         },
    {&EV_UIPulldownMenuContainer_PopupBGColor,          &UIPulldownMenuContainer::SetPopupBGColor         },
    {&EV_UIPulldownMenuContainer_HighlightFGColor,      &UIPulldownMenuContainer::SetHighlightFGColor     },
    {&EV_UIPulldownMenuContainer_HighlightBGColor,      &UIPulldownMenuContainer::SetHighlightBGColor     },
    {&EV_Layout_VirtualRes,                             &UIPulldownMenuContainer::PulldownVirtualRes      },
    {NULL,                                              NULL                                              }
};

UIPulldownMenuContainer::UIPulldownMenuContainer()
{
    m_menu = new UIPulldownMenu();
    m_menu->CreateAligned(this, this);
}

UIPulldownMenuContainer::~UIPulldownMenuContainer()
{
    for (int i = m_popups.NumObjects(); i > 0; i--) {
        uipopup_describe *uipd = m_popups.ObjectAt(i);
        m_popups.RemoveObjectAt(i);
        delete uipd;
    }

    for (int i = m_dataContainer.NumObjects(); i > 0; i--) {
        char *data = m_dataContainer.ObjectAt(i);
        m_dataContainer.RemoveObjectAt(i);
        delete data;
    }

    // FIXME: m_menu isn't deleted, possible memory leak!
}

void UIPulldownMenuContainer::FrameInitialized(void)
{
    AllowActivate(qfalse);
    m_menu->setBackgroundColor(m_background_color, qtrue);
    m_menu->setForegroundColor(m_foreground_color);
}

void UIPulldownMenuContainer::setBackgroundAlpha(float f)
{
    m_alpha = f;
    m_menu->setBackgroundAlpha(f);
}

void UIPulldownMenuContainer::setBackgroundColor(const UColor& color, bool setbordercolor)
{
    UIWidget::setBackgroundColor(color, setbordercolor);
    m_menu->setBackgroundColor(color, setbordercolor);
}

void UIPulldownMenuContainer::setForegroundColor(const UColor& color)
{
    UIWidget::setForegroundColor(color);
    m_menu->setForegroundColor(color);
}

void UIPulldownMenuContainer::SetPopupHighlightFGColor(Event *ev)
{
    str   menu = ev->GetString(1);
    float r    = ev->GetFloat(2);
    float g    = ev->GetFloat(3);
    float b    = ev->GetFloat(4);
    float a    = ev->GetFloat(5);

    m_menu->setPopupHighlightFGColor(menu, UColor(r, g, b, a));
}

void UIPulldownMenuContainer::SetPopupHighlightBGColor(Event *ev)
{
    str   menu = ev->GetString(1);
    float r    = ev->GetFloat(2);
    float g    = ev->GetFloat(3);
    float b    = ev->GetFloat(4);
    float a    = ev->GetFloat(5);

    m_menu->setPopupHighlightBGColor(menu, UColor(r, g, b, a));
}

void UIPulldownMenuContainer::SetPopupFGColor(Event *ev)
{
    str   menu = ev->GetString(1);
    float r    = ev->GetFloat(2);
    float g    = ev->GetFloat(3);
    float b    = ev->GetFloat(4);
    float a    = ev->GetFloat(5);

    m_menu->setPopupFGColor(menu, UColor(r, g, b, a));
}

void UIPulldownMenuContainer::SetPopupBGColor(Event *ev)
{
    str   menu = ev->GetString(1);
    float r    = ev->GetFloat(2);
    float g    = ev->GetFloat(3);
    float b    = ev->GetFloat(4);
    float a    = ev->GetFloat(5);

    m_menu->setPopupBGColor(menu, UColor(r, g, b, a));
}

void UIPulldownMenuContainer::SetHighlightFGColor(Event *ev)
{
    // original game goes 1-4 for some reason
    float r = ev->GetFloat(2);
    float g = ev->GetFloat(3);
    float b = ev->GetFloat(4);
    float a = ev->GetFloat(5);

    m_menu->setHighlightFGColor(UColor(r, g, b, a));
}

void UIPulldownMenuContainer::SetHighlightBGColor(Event *ev)
{
    // original game goes 1-4 for some reason
    float r = ev->GetFloat(2);
    float g = ev->GetFloat(3);
    float b = ev->GetFloat(4);
    float a = ev->GetFloat(5);

    m_menu->setHighlightBGColor(UColor(r, g, b, a));
}

void UIPulldownMenuContainer::SetMenuShader(Event *ev)
{
    str               menu   = ev->GetString(1);
    str               shader = ev->GetString(2);
    UIReggedMaterial *mat    = uWinMan.RegisterShader(shader);
    m_menu->setPulldownShader(menu, mat);
}

void UIPulldownMenuContainer::SetSelectedMenuShader(Event *ev)
{
    str               menu   = ev->GetString(1);
    str               shader = ev->GetString(2);
    UIReggedMaterial *mat    = uWinMan.RegisterShader(shader);
    m_menu->setSelectedPulldownShader(menu, mat);
}

void UIPulldownMenuContainer::Realign(void)
{
    UIWidget::Realign();
    m_menu->Realign();
}

void UIPulldownMenuContainer::PulldownVirtualRes(Event *ev)
{
    LayoutVirtualRes(ev);

    if (m_bVirtual) {
        Event *newEv = new Event(EV_Layout_VirtualRes);
        newEv->AddInteger(1);
        m_menu->ProcessEvent(newEv);
    }
}

void UIPulldownMenuContainer::AddPopup(Event *ev)
{
    str menu  = ev->GetString(1);
    str title = ev->GetString(2);
    str t     = ev->GetString(3);
    str d     = ev->GetString(4);

    uipopup_type type = UI_PopupTypeStringToInt(t);

    // Make sure to create a duplicate of the original string,
    // otherwise `data` will point to junk when `d` is destroyed.
    // This only seems to run for each popup menu during game startup,
    // so it doesn't appear to leak memory continuously,
    // but it's being cleaned up in uipopup_describe's dtor anyway.
    void *data = strdup(d);

    uipopup_describe *uipd = new uipopup_describe(title, type, data, NULL);
    m_popups.AddObject(uipd);
    m_menu->AddUIPopupDescribe(menu, uipd);
}

// Added in OpenMOHAA Plus: a cvar's latched value if a restart is pending (cl_renderer), else its value
static str PulldownCvarValue(const char *name)
{
    const cvar_t *cvar = uii.Cvar_Find(name);

    if (cvar && cvar->latchedString) {
        return cvar->latchedString;
    }
    return uii.Cvar_GetString(name, "");
}

// Added in OpenMOHAA Plus: values compare as numbers when both are numbers ("1.0" and "1"), else
//  case-insensitively; one pair of surrounding quotes is ignored
static bool PulldownValuesEqual(const char *a, const char *b)
{
    char        unquoted[MAX_STRING_CHARS];
    size_t      len = strlen(a);
    char       *enda, *endb;
    double      na, nb;

    if (len >= 2 && a[0] == '"' && a[len - 1] == '"') {
        Q_strncpyz(unquoted, a + 1, len - 1 < sizeof(unquoted) ? len - 1 : sizeof(unquoted));
        a = unquoted;
    }

    na = strtod(a, &enda);
    nb = strtod(b, &endb);
    if (*a && *b && !*enda && !*endb) {
        return na == nb;
    }
    return !Q_stricmp(a, b);
}

// Added in OpenMOHAA Plus: with a "linkcvar", the title of the first item whose command has at
//  least one "set|seta <cvar> <value>" and whose every such command matches that cvar's current
//  (or latched) value; a "reset <cvar>" command matches while that cvar is at its default; other
//  commands are ignored. The bare value of the linked cvar if no item matches; empty without
//  linkcvar
str UIPulldownMenuContainer::getValueTitle(void) const
{
    if (!m_cvarname.length()) {
        return "";
    }

    for (int i = 1; i <= m_popups.NumObjects(); i++) {
        const uipopup_describe *uipd = m_popups.ObjectAt(i);
        char                    commands[MAX_STRING_CHARS];
        char                   *segment, *next;
        bool                    any = false, all = true;

        if (uipd->type != UIP_CMD && uipd->type != UIP_CVAR) {
            continue;
        }

        Q_strncpyz(commands, (const char *)uipd->data, sizeof(commands));
        for (segment = commands; segment && all; segment = next) {
            char keyword[64], name[MAX_STRING_CHARS], value[MAX_STRING_CHARS];
            int  fields;

            next = strchr(segment, ';');
            if (next) {
                *next++ = 0;
            }

            value[0] = 0;
            fields   = sscanf(segment, " %63s %1023s %1023[^\n]", keyword, name, value);
            if (fields >= 2 && !Q_stricmp(keyword, "reset")) {
                const cvar_t *cvar = uii.Cvar_Find(name);
                any                = true;
                all                = cvar && !strcmp(PulldownCvarValue(name).c_str(), cvar->resetString);
            } else if (fields >= 2 && (!Q_stricmp(keyword, "set") || !Q_stricmp(keyword, "seta"))) {
                char  *trim = value + strlen(value);
                while (trim > value && trim[-1] == ' ') {
                    *--trim = 0;
                }
                any = true;
                all = PulldownValuesEqual(value, PulldownCvarValue(name).c_str());
            }
        }

        if (any && all) {
            return uipd->title;
        }
    }

    return PulldownCvarValue(m_cvarname.c_str());
}

// Added in OpenMOHAA Plus: the pulldown shows the current value (see getValueTitle) in this
//  widget's font; the container itself draws nothing, as before
void UIPulldownMenuContainer::Draw(void)
{
    m_menu->setValue(getValueTitle(), m_font);
}

// Added in OpenMOHAA Plus: "ui_printwidgets"; the value is set first so the pulldown (a child)
//  prints what the next frame draws
void UIPulldownMenuContainer::PrintGeometry(int depth)
{
    m_menu->setValue(getValueTitle(), m_font);
    UIWidget::PrintGeometry(depth);
}
