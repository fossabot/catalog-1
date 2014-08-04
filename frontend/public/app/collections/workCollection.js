/* Catalog web application - Backbone collection of works
 *
 * Copyright 2014 Commons Machinery http://commonsmachinery.se/
 * Distributed under an AGPL_v3 license, please see LICENSE in the top dir.
 */

define(['lib/backbone', 'lib/backbone.paginator', 'models/workModel'],
       function(Backbone, Paginator, Work)
{
    'use strict';

    var WorkCollection = Backbone.PageableCollection.extend({
        model: Work,
        url: '/works',

        state: {
            firstPage: 1,
            pageSize: 12
        },

        queryParams: {
            sortKey: 'sort'
        },

        initialize: function(){
            var page;
            if(window.location.search){
                var page = window.location.search.match(/page=(\d+)/)[1]
                if(page){
                    this.state.currentPage = Number(page);
                }
            }
        }
    });

    return WorkCollection;
});